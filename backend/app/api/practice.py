"""Practice HTTP surface (single-part + whole-section).

Endpoints:
  GET   /tests/{test_id}/practice-units                                — pick screen
  POST  /tests/{test_id}/practice-attempts                             — start + enter
  GET   /admin/tests/{test_id}/practice-parts                          — admin table
  PATCH /admin/tests/{test_id}/practice-parts/{section_type}/{part}    — admin edit
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Actor, get_current_actor, get_current_admin
from app.core.database import get_db
from app.models.attempt import Attempt, AttemptMode, AttemptStatus
from app.models.section import Section, SectionType
from app.models.section_progress import SectionProgress
from app.models.test import Test
from app.schemas.attempt import AttemptRead
from app.schemas.practice import (
    PracticePartSettingsRead,
    PracticePartSettingsUpdate,
    PracticeSectionUnitRead,
    PracticeUnitLastAttempt,
    PracticeUnitRead,
    PracticeUnitsResponse,
    StartPracticeAttemptRequest,
)
from app.services import practice_parts
from app.services import section_progress as sp
from app.services import section_settings as settings_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Practice"])

_VALID_TYPES = {t.value for t in SectionType}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _status_str(status_val) -> str:
    return status_val if isinstance(status_val, str) else status_val.value


def _band_for_attempt(attempt: Attempt, section_type: str | None) -> float | None:
    if section_type == SectionType.LISTENING.value:
        return attempt.listening_band
    if section_type == SectionType.READING.value:
        return attempt.reading_band
    if section_type == SectionType.WRITING.value:
        return attempt.writing_band
    if section_type == SectionType.SPEAKING.value:
        return attempt.speaking_band
    return None


async def _load_test_or_404(
    db: AsyncSession,
    test_id: uuid.UUID,
    actor: Actor,
) -> Test:
    test = await db.get(Test, test_id)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    if actor.role == "student" and not test.is_published:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Test not available")
    return test


async def _load_last_part_attempts(
    db: AsyncSession,
    user_id: uuid.UUID,
    test_id: uuid.UUID,
) -> dict[tuple[str, int], PracticeUnitLastAttempt]:
    """Latest single-part practice attempt per (section_type, part_number)."""
    result = await db.execute(
        select(Attempt)
        .where(
            Attempt.user_id == user_id,
            Attempt.test_id == test_id,
            Attempt.mode == AttemptMode.SINGLE_PART.value,
        )
        .order_by(Attempt.created_at.desc())
    )
    attempts = list(result.scalars().all())
    if not attempts:
        return {}

    latest: dict[tuple[str, int], PracticeUnitLastAttempt] = {}
    for attempt in attempts:
        stype = attempt.practice_section_type
        part = attempt.practice_part_number
        if stype is None or part is None:
            continue
        key = (stype, part)
        if key in latest:
            continue
        latest[key] = PracticeUnitLastAttempt(
            attempt_id=attempt.id,
            status=_status_str(attempt.status),
            finished_at=attempt.finished_at,
            correct=attempt.practice_correct,
            total=attempt.practice_total,
            band=None,  # single-part is raw-only
        )
    return latest


async def _load_last_section_attempts(
    db: AsyncSession,
    user_id: uuid.UUID,
    test_id: uuid.UUID,
) -> dict[str, PracticeUnitLastAttempt]:
    """Latest whole-section practice attempt per section_type."""
    result = await db.execute(
        select(Attempt)
        .where(
            Attempt.user_id == user_id,
            Attempt.test_id == test_id,
            Attempt.mode == AttemptMode.SINGLE_SECTION.value,
        )
        .order_by(Attempt.created_at.desc())
    )
    attempts = list(result.scalars().all())
    latest: dict[str, PracticeUnitLastAttempt] = {}
    for attempt in attempts:
        stype = attempt.practice_section_type
        if stype is None or stype in latest:
            continue
        latest[stype] = PracticeUnitLastAttempt(
            attempt_id=attempt.id,
            status=_status_str(attempt.status),
            finished_at=attempt.finished_at,
            correct=attempt.practice_correct,
            total=attempt.practice_total,
            band=_band_for_attempt(attempt, stype),
        )
    return latest


async def _enter_practice(
    db: AsyncSession,
    attempt: Attempt,
    test_id: uuid.UUID,
    section_type: str,
    now: datetime,
    *,
    duration_override: int | None,
) -> None:
    for row in sp.ensure_progress_rows(attempt.id, present_types=[section_type]):
        db.add(row)
    await db.flush()

    rows_result = await db.execute(
        select(SectionProgress)
        .where(SectionProgress.attempt_id == attempt.id)
        .with_for_update()
    )
    rows = list(rows_result.scalars().all())
    settings = await settings_service.ensure_settings(db, test_id)

    try:
        sp.apply_enter(
            rows,
            settings,
            section_type,
            now,
            present_types=[section_type],
            duration_override_minutes=duration_override,
        )
    except sp.SectionConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.detail) from exc


@router.get("/tests/{test_id}/practice-units", response_model=PracticeUnitsResponse)
async def list_practice_units(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """Enumerate all practice-addressable parts and whole-section units."""
    await _load_test_or_404(db, test_id, actor)
    units = await practice_parts.enumerate_units(db, test_id)
    section_units = await practice_parts.enumerate_section_units(db, test_id)

    last_parts: dict[tuple[str, int], PracticeUnitLastAttempt] = {}
    last_sections: dict[str, PracticeUnitLastAttempt] = {}
    if actor.user_id is not None:
        last_parts = await _load_last_part_attempts(db, actor.user_id, test_id)
        last_sections = await _load_last_section_attempts(db, actor.user_id, test_id)

    return PracticeUnitsResponse(
        test_id=test_id,
        units=[
            PracticeUnitRead(
                section_type=unit.section_type,
                part_number=unit.part_number,
                section_id=unit.section_id,
                label=unit.label,
                question_count=unit.question_count,
                duration_minutes=unit.duration_minutes,
                duration_is_default=unit.duration_is_default,
                is_enabled=unit.is_enabled,
                last_attempt=last_parts.get((unit.section_type, unit.part_number)),
            )
            for unit in units
        ],
        sections=[
            PracticeSectionUnitRead(
                section_type=unit.section_type,
                label=unit.label,
                part_count=unit.part_count,
                question_count=unit.question_count,
                duration_minutes=unit.duration_minutes,
                is_enabled=unit.is_enabled,
                last_attempt=last_sections.get(unit.section_type),
            )
            for unit in section_units
        ],
    )


@router.post(
    "/tests/{test_id}/practice-attempts",
    response_model=AttemptRead,
    status_code=status.HTTP_201_CREATED,
)
async def start_practice_attempt(
    test_id: uuid.UUID,
    payload: StartPracticeAttemptRequest,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """Create a practice attempt and enter its target section in one call."""
    if payload.section_type not in _VALID_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid section type")

    await _load_test_or_404(db, test_id, actor)

    if payload.scope == "section":
        return await _start_section_practice(db, test_id, payload, actor)
    return await _start_part_practice(db, test_id, payload, actor)


async def _start_part_practice(
    db: AsyncSession,
    test_id: uuid.UUID,
    payload: StartPracticeAttemptRequest,
    actor: Actor,
) -> Attempt:
    assert payload.part_number is not None
    unit = await practice_parts.find_unit(
        db, test_id, payload.section_type, payload.part_number
    )
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Practice unit not found")
    if not unit.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This part is not available for practice",
        )
    if unit.question_count == 0 and payload.section_type != SectionType.SPEAKING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This part has no questions to practice",
        )

    if actor.user_id is not None:
        existing_result = await db.execute(
            select(Attempt).where(
                Attempt.user_id == actor.user_id,
                Attempt.test_id == test_id,
                Attempt.status == AttemptStatus.IN_PROGRESS,
                Attempt.mode == AttemptMode.SINGLE_PART.value,
                Attempt.practice_section_id == unit.section_id,
                Attempt.practice_part_number == unit.part_number,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing is not None:
            existing._practice_section_cache = await db.get(Section, unit.section_id)
            return existing

    now = _now()
    attempt = Attempt(
        test_id=test_id,
        user_id=actor.user_id,
        status=AttemptStatus.IN_PROGRESS,
        mode=AttemptMode.SINGLE_PART.value,
        practice_section_id=unit.section_id,
        practice_part_number=unit.part_number,
        practice_section_type=unit.section_type,
        started_at=now,
    )
    db.add(attempt)
    try:
        await db.flush()
        duration_override = practice_parts.duration_for_practice_attempt(unit)
        await _enter_practice(
            db,
            attempt,
            test_id,
            unit.section_type,
            now,
            duration_override=duration_override,
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        if actor.user_id is None:
            raise
        raced = await db.execute(
            select(Attempt).where(
                Attempt.user_id == actor.user_id,
                Attempt.test_id == test_id,
                Attempt.status == AttemptStatus.IN_PROGRESS,
                Attempt.mode == AttemptMode.SINGLE_PART.value,
                Attempt.practice_section_id == unit.section_id,
                Attempt.practice_part_number == unit.part_number,
            )
        )
        existing = raced.scalar_one_or_none()
        if existing is None:
            raise
        existing._practice_section_cache = await db.get(Section, unit.section_id)
        return existing

    await db.refresh(attempt)
    attempt._practice_section_cache = await db.get(Section, unit.section_id)
    return attempt


async def _start_section_practice(
    db: AsyncSession,
    test_id: uuid.UUID,
    payload: StartPracticeAttemptRequest,
    actor: Actor,
) -> Attempt:
    unit = await practice_parts.find_section_unit(db, test_id, payload.section_type)
    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found in this test",
        )
    if not unit.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This section is not available for practice",
        )
    if unit.question_count == 0 and payload.section_type != SectionType.SPEAKING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This section has no questions to practice",
        )

    if actor.user_id is not None:
        existing_result = await db.execute(
            select(Attempt).where(
                Attempt.user_id == actor.user_id,
                Attempt.test_id == test_id,
                Attempt.status == AttemptStatus.IN_PROGRESS,
                Attempt.mode == AttemptMode.SINGLE_SECTION.value,
                Attempt.practice_section_type == payload.section_type,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing is not None:
            return existing

    now = _now()
    attempt = Attempt(
        test_id=test_id,
        user_id=actor.user_id,
        status=AttemptStatus.IN_PROGRESS,
        mode=AttemptMode.SINGLE_SECTION.value,
        practice_section_id=None,
        practice_part_number=None,
        practice_section_type=payload.section_type,
        started_at=now,
    )
    db.add(attempt)
    try:
        await db.flush()
        # Whole-section uses TestSectionSettings duration (override=None).
        await _enter_practice(
            db,
            attempt,
            test_id,
            payload.section_type,
            now,
            duration_override=None,
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        if actor.user_id is None:
            raise
        raced = await db.execute(
            select(Attempt).where(
                Attempt.user_id == actor.user_id,
                Attempt.test_id == test_id,
                Attempt.status == AttemptStatus.IN_PROGRESS,
                Attempt.mode == AttemptMode.SINGLE_SECTION.value,
                Attempt.practice_section_type == payload.section_type,
            )
        )
        existing = raced.scalar_one_or_none()
        if existing is None:
            raise
        return existing

    await db.refresh(attempt)
    return attempt


# ── Admin endpoints ─────────────────────────────────────────────────────────


@router.get(
    "/admin/tests/{test_id}/practice-parts",
    response_model=list[PracticePartSettingsRead],
)
async def list_admin_practice_parts(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: Actor = Depends(get_current_admin),
):
    """Admin view — every part with its custom setting (or the default it would use)."""
    units = await practice_parts.enumerate_units(db, test_id)
    return [
        PracticePartSettingsRead(
            section_type=unit.section_type,
            part_number=unit.part_number,
            duration_minutes=None if unit.duration_is_default else unit.duration_minutes,
            is_enabled=unit.is_enabled,
            effective_duration_minutes=unit.duration_minutes,
        )
        for unit in units
    ]


@router.patch(
    "/admin/tests/{test_id}/practice-parts/{section_type}/{part_number}",
    response_model=PracticePartSettingsRead,
)
async def update_admin_practice_part(
    test_id: uuid.UUID,
    section_type: str,
    part_number: int,
    payload: PracticePartSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _: Actor = Depends(get_current_admin),
):
    if section_type not in _VALID_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid section type")
    if part_number < 1 or part_number > 20:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid part number")

    unit = await practice_parts.find_unit(db, test_id, section_type, part_number)
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Practice unit not found")

    if payload.duration_minutes is not None:
        if payload.duration_minutes < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duration must be at least 1 minute",
            )
        if section_type != SectionType.SPEAKING.value and payload.duration_minutes > 120:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duration must not exceed 120 minutes",
            )

    await practice_parts.upsert_setting(
        db,
        test_id,
        section_type,
        part_number,
        duration_minutes=payload.duration_minutes,
        is_enabled=payload.is_enabled,
    )
    await db.commit()

    refreshed = await practice_parts.find_unit(db, test_id, section_type, part_number)
    assert refreshed is not None
    return PracticePartSettingsRead(
        section_type=refreshed.section_type,
        part_number=refreshed.part_number,
        duration_minutes=None if refreshed.duration_is_default else refreshed.duration_minutes,
        is_enabled=refreshed.is_enabled,
        effective_duration_minutes=refreshed.duration_minutes,
    )
