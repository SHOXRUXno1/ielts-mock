"""Blind full-mock assignment for students.

The student never picks a Cambridge booklet. The server hands them one
published test, remembers it for resume, and prefers a paper they have
not sat yet. After every paper has been sat they can still Start — a
random published paper is drawn again. Student-facing titles never
include book names.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.answer import Answer
from app.models.attempt import Attempt, AttemptMode, AttemptStatus
from app.models.question import Question
from app.models.section import Section
from app.models.section_progress import SectionProgress
from app.models.test import Test
from app.models.user import User
from app.schemas.test import TestDetailRead
from app.services import section_progress as sp
from app.utils.labels import format_test_label


class NoUnusedMocks(Exception):
    """No published test exists to assign."""


def student_mock_label(slot: int | None) -> str:
    if slot is None:
        return "Full mock"
    return f"Mock #{slot}"


def practice_set_label(slot: int | None) -> str:
    if slot is None:
        return "Practice set"
    return f"Practice set #{slot}"


def pick_unused_id(
    published_ids: list[uuid.UUID],
    used_ids: set[uuid.UUID],
) -> uuid.UUID | None:
    pool = [tid for tid in published_ids if tid not in used_ids]
    if not pool:
        return None
    return secrets.choice(pool)


def pick_next_id(
    published_ids: list[uuid.UUID],
    used_ids: set[uuid.UUID],
) -> uuid.UUID | None:
    """Prefer an unseen paper; once the set is exhausted, recycle at random."""
    unused = pick_unused_id(published_ids, used_ids)
    if unused is not None:
        return unused
    if not published_ids:
        return None
    return secrets.choice(published_ids)


def cloak_test_read(detail: TestDetailRead, title: str) -> TestDetailRead:
    return detail.model_copy(
        update={
            "title": title,
            "description": None,
            "book_name": None,
            "book_slug": "mock",
            "test_number": 0,
        }
    )


async def slot_map_for_user(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> dict[uuid.UUID, int]:
    """Stable Mock #N per student, in the order they first sat each test."""
    stmt = (
        select(Attempt.test_id, func.min(Attempt.created_at).label("first_at"))
        .where(
            Attempt.user_id == user_id,
            Attempt.mode == AttemptMode.FULL_MOCK.value,
        )
        .group_by(Attempt.test_id)
        .order_by(func.min(Attempt.created_at).asc())
    )
    rows = (await db.execute(stmt)).all()
    return {row.test_id: index for index, row in enumerate(rows, start=1)}


async def label_for_user_test(
    db: AsyncSession,
    user_id: uuid.UUID,
    test_id: uuid.UUID,
) -> str:
    slots = await slot_map_for_user(db, user_id)
    return student_mock_label(slots.get(test_id))


async def used_full_mock_test_ids(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> set[uuid.UUID]:
    rows = await db.execute(
        select(Attempt.test_id).where(
            Attempt.user_id == user_id,
            Attempt.mode == AttemptMode.FULL_MOCK.value,
        )
    )
    return {row[0] for row in rows.all()}


async def in_progress_full_mock(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> Attempt | None:
    result = await db.execute(
        select(Attempt)
        .where(
            Attempt.user_id == user_id,
            Attempt.mode == AttemptMode.FULL_MOCK.value,
            Attempt.status == AttemptStatus.IN_PROGRESS,
        )
        .order_by(Attempt.updated_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def published_test_ids(db: AsyncSession) -> list[uuid.UUID]:
    rows = await db.execute(
        select(Test.id)
        .where(Test.is_published.is_(True))
        .order_by(Test.created_at.asc())
    )
    return [row[0] for row in rows.all()]


async def resume_section_for_attempt(
    db: AsyncSession,
    attempt_id: uuid.UUID,
) -> str | None:
    rows = (
        await db.execute(
            select(SectionProgress).where(SectionProgress.attempt_id == attempt_id)
        )
    ).scalars().all()
    return sp.resume_section_type(list(rows))


def _section_type_value(value: object) -> str:
    return value.value if hasattr(value, "value") else str(value)


async def resume_part_for_attempt(
    db: AsyncSession,
    attempt: Attempt,
    section_type: str,
) -> int | None:
    if section_type == "speaking":
        return None
    answered = set(
        (
            await db.execute(
                select(Answer.question_id).where(Answer.attempt_id == attempt.id)
            )
        ).scalars().all()
    )
    sections = list(
        (
            await db.execute(
                select(Section)
                .where(Section.test_id == attempt.test_id)
                .order_by(Section.order.asc())
            )
        ).scalars().all()
    )
    skill_sections = [s for s in sections if _section_type_value(s.type) == section_type]
    if not skill_sections:
        return 1

    if section_type == "writing":
        writing = skill_sections[0]
        questions = list(
            (
                await db.execute(
                    select(Question)
                    .where(Question.section_id == writing.id)
                    .order_by(Question.order.asc())
                )
            ).scalars().all()
        )
        by_task: dict[int, list[uuid.UUID]] = {}
        for q in questions:
            qtype = _section_type_value(q.question_type)
            if qtype != "essay":
                continue
            task = q.task_number if q.task_number in (1, 2) else (
                q.order if q.order in (1, 2) else None
            )
            if task is None:
                continue
            by_task.setdefault(task, []).append(q.id)
        part_qids = [by_task[t] for t in sorted(by_task)]
    else:
        part_qids = []
        for skill_section in skill_sections:
            qids = list(
                (
                    await db.execute(
                        select(Question.id).where(Question.section_id == skill_section.id)
                    )
                ).scalars().all()
            )
            part_qids.append(qids)
    return sp.resume_part_number(section_type, part_qids, answered)


async def resume_position_for_attempt(
    db: AsyncSession,
    attempt_id: uuid.UUID,
) -> tuple[str | None, int | None]:
    attempt = await db.get(Attempt, attempt_id)
    section = await resume_section_for_attempt(db, attempt_id)
    if attempt is None or section is None:
        return section, None
    return section, await resume_part_for_attempt(db, attempt, section)


async def remaining_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    published = await published_test_ids(db)
    used = await used_full_mock_test_ids(db, user_id)
    return sum(1 for tid in published if tid not in used)


async def published_index_map(db: AsyncSession) -> dict[uuid.UUID, int]:
    ids = await published_test_ids(db)
    return {tid: index for index, tid in enumerate(ids, start=1)}


async def practice_label_for_test(db: AsyncSession, test_id: uuid.UUID) -> str:
    indexes = await published_index_map(db)
    return practice_set_label(indexes.get(test_id))


async def latest_full_mock_picked(
    db: AsyncSession,
    user_id: uuid.UUID,
    test_id: uuid.UUID,
) -> bool:
    """True when the student's most recent full mock on this paper was a
    deliberate pick. A later random sitting on the same paper flips it back,
    so the label always reflects how the current attempt was started.
    """
    row = (
        await db.execute(
            select(Attempt.picked)
            .where(
                Attempt.user_id == user_id,
                Attempt.test_id == test_id,
                Attempt.mode == AttemptMode.FULL_MOCK.value,
            )
            .order_by(Attempt.created_at.desc())
            .limit(1)
        )
    ).first()
    return bool(row[0]) if row is not None else False


async def student_facing_title(
    db: AsyncSession,
    user_id: uuid.UUID,
    test_id: uuid.UUID,
    *,
    kind: Literal["auto", "mock", "practice"] = "auto",
) -> str:
    if kind == "practice":
        return await practice_label_for_test(db, test_id)
    if kind == "mock":
        return await label_for_user_test(db, user_id, test_id)
    # auto: a deliberately-picked paper is named by its catalogue number, so
    # the student sees the very paper they chose; random mocks stay "Mock #N".
    if await latest_full_mock_picked(db, user_id, test_id):
        return await practice_label_for_test(db, test_id)
    slots = await slot_map_for_user(db, user_id)
    if test_id in slots:
        return student_mock_label(slots[test_id])
    return await practice_label_for_test(db, test_id)


async def title_for_actor(
    db: AsyncSession,
    *,
    role: str,
    user_id: uuid.UUID | None,
    test_id: uuid.UUID,
    real_title: str,
    test_number: int | None,
    kind: Literal["auto", "mock", "practice"] = "auto",
) -> str:
    if role != "student" or user_id is None:
        return format_test_label(real_title, test_number)
    return await student_facing_title(db, user_id, test_id, kind=kind)


async def start_next_full_mock(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> Attempt:
    """Resume a live sitting, or assign the next published paper and start it."""
    locked = (
        await db.execute(select(User).where(User.id == user_id).with_for_update())
    ).scalar_one_or_none()
    if locked is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    live = await in_progress_full_mock(db, user_id)
    if live is not None:
        return live

    used = await used_full_mock_test_ids(db, user_id)
    published = await published_test_ids(db)
    test_id = pick_next_id(published, used)
    if test_id is None:
        raise NoUnusedMocks

    test = await db.get(Test, test_id)
    if test is None or not test.is_published:
        raise NoUnusedMocks
    # Do not call section_settings.ensure_loaded here. db.get() leaves
    # test.section_settings unloaded; touching it in async raises
    # MissingGreenlet (500). start_attempt never needed settings to
    # create the sitting, and a commit inside ensure_loaded would also
    # release this FOR UPDATE lock mid-start.

    attempt = Attempt(
        test_id=test_id,
        user_id=user_id,
        status=AttemptStatus.IN_PROGRESS,
        mode=AttemptMode.FULL_MOCK.value,
        started_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    try:
        await db.flush()
        for row in sp.ensure_progress_rows(attempt.id):
            db.add(row)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raced = await in_progress_full_mock(db, user_id)
        if raced is None:
            raise
        return raced

    await db.refresh(attempt)
    return attempt


async def start_full_mock_on_test(
    db: AsyncSession,
    user_id: uuid.UUID,
    test_id: uuid.UUID,
) -> Attempt:
    """Start (or resume) a full mock on a specific paper the caller picked.

    Same guards as start_next_full_mock — one in-progress full mock per
    student, idempotent when the live sitting is already on this test, and
    the row-level user lock prevents parallel starts from opening two
    attempts on different tests at once.
    """
    locked = (
        await db.execute(select(User).where(User.id == user_id).with_for_update())
    ).scalar_one_or_none()
    if locked is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    live = await in_progress_full_mock(db, user_id)
    if live is not None:
        if live.test_id == test_id:
            # Resuming the paper the student is explicitly picking — mark it
            # picked so the exam screen names it "Practice set #N" even if the
            # live sitting was opened before pick-tracking existed.
            if not live.picked:
                live.picked = True
                await db.commit()
                await db.refresh(live)
            return live
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a full mock in progress on another paper.",
        )

    test = await db.get(Test, test_id)
    if test is None or not test.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found or not published.",
        )

    attempt = Attempt(
        test_id=test_id,
        user_id=user_id,
        status=AttemptStatus.IN_PROGRESS,
        mode=AttemptMode.FULL_MOCK.value,
        started_at=datetime.now(timezone.utc),
        picked=True,
    )
    db.add(attempt)
    try:
        await db.flush()
        for row in sp.ensure_progress_rows(attempt.id):
            db.add(row)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raced = await in_progress_full_mock(db, user_id)
        if raced is None:
            raise
        return raced

    await db.refresh(attempt)
    return attempt


def http_no_mocks() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="No published full mocks are available",
    )
