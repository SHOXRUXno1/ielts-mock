import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Actor, get_current_student
from app.core.database import get_db
from app.models.answer import Answer
from app.models.attempt import Attempt, AttemptMode, AttemptStatus, PRACTICE_MODES
from app.models.question import Question
from app.models.section import Section
from app.models.test import Test
from app.services import section_settings as settings_service
from app.services.section_settings import timed_total_minutes
from app.schemas.attempt import AttemptRead
from app.services.student_mock import (
    NoUnusedMocks,
    http_no_mocks,
    in_progress_full_mock,
    practice_set_label,
    published_index_map,
    published_test_ids,
    remaining_count,
    resume_section_for_attempt,
    slot_map_for_user,
    start_next_full_mock,
    student_mock_label,
)


def _practice_band_for(att: Attempt, section_type: str | None) -> float | None:
    if section_type == "listening":
        return att.listening_band
    if section_type == "reading":
        return att.reading_band
    if section_type == "writing":
        return att.writing_band
    if section_type == "speaking":
        return att.speaking_band
    return None

router = APIRouter(prefix="/student", tags=["Student Panel"])


class DashboardAttempt(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    test_id: uuid.UUID
    test_title: str
    overall_band: float | None
    status: str
    finished_at: datetime | None
    created_at: datetime


class BandTrendPoint(BaseModel):
    attempt_id: uuid.UUID
    band: float
    date: datetime


class SectionBands(BaseModel):
    listening: float | None = None
    reading: float | None = None
    writing: float | None = None
    speaking: float | None = None


class InProgressAttempt(BaseModel):
    id: uuid.UUID
    test_id: uuid.UUID
    test_title: str
    answered: int
    total: int
    updated_at: datetime
    section: str | None = None


class DashboardResponse(BaseModel):
    tests_taken: int
    avg_band: float | None
    best_band: float | None
    section_bands: SectionBands
    band_trend: list[BandTrendPoint]
    in_progress: InProgressAttempt | None
    recent: list[DashboardAttempt]


# ── Catalog schemas ───────────────────────────────────────────────────────────

class SectionProgress(BaseModel):
    score: float | None
    completed: bool


class CatalogTest(BaseModel):
    id: uuid.UUID
    title: str
    book_name: str | None = None
    test_type: str = "academic"
    duration_minutes: int = 0
    section_count: int = 0
    sections: dict[str, SectionProgress]
    overall_score: float | None
    status: str = "new"
    in_progress_attempt_id: uuid.UUID | None = None
    last_attempt_at: str | None = None


class TestGroup(BaseModel):
    name: str
    tests: list[CatalogTest]


class CatalogResponse(BaseModel):
    groups: list[TestGroup]


# kept for backwards-compat if anything still references it
class TestListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    type: str
    already_attempted: bool
    best_band: float | None
    in_progress_attempt_id: uuid.UUID | None = None


class FullMockStatus(BaseModel):
    remaining: int
    total_published: int
    in_progress_attempt_id: uuid.UUID | None = None
    in_progress_test_id: uuid.UUID | None = None
    in_progress_title: str | None = None
    in_progress_section: str | None = None


@router.get("/dashboard", response_model=DashboardResponse)
async def student_dashboard(
    actor: Actor = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    finished_statuses = [
        AttemptStatus.COMPLETED,
        AttemptStatus.AUTO_SCORED,
        AttemptStatus.FULLY_SCORED,
        AttemptStatus.COMPLETED_WITHOUT_SPEAKING,
    ]

    stmt = (
        select(Attempt, Test.title, Test.test_number)
        .join(Test, Attempt.test_id == Test.id)
        .where(
            Attempt.user_id == actor.user_id,
            Attempt.mode == AttemptMode.FULL_MOCK.value,
            Attempt.status.in_(finished_statuses),
        )
        .order_by(Attempt.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    slots = await slot_map_for_user(db, actor.user_id)

    bands = [r.Attempt.overall_band for r in rows if r.Attempt.overall_band is not None]
    recent = [
        DashboardAttempt(
            id=r.Attempt.id,
            test_id=r.Attempt.test_id,
            test_title=student_mock_label(slots.get(r.Attempt.test_id)),
            overall_band=r.Attempt.overall_band,
            status=r.Attempt.status,
            finished_at=r.Attempt.finished_at,
            created_at=r.Attempt.created_at,
        )
        for r in rows[:5]
    ]

    # Section band averages across all finished attempts
    l_bands = [r.Attempt.listening_band for r in rows if r.Attempt.listening_band is not None]
    r_bands = [r.Attempt.reading_band for r in rows if r.Attempt.reading_band is not None]
    w_bands = [r.Attempt.writing_band for r in rows if r.Attempt.writing_band is not None]
    s_bands = [r.Attempt.speaking_band for r in rows if r.Attempt.speaking_band is not None]
    section_bands = SectionBands(
        listening=round(sum(l_bands) / len(l_bands), 1) if l_bands else None,
        reading=round(sum(r_bands) / len(r_bands), 1) if r_bands else None,
        writing=round(sum(w_bands) / len(w_bands), 1) if w_bands else None,
        speaking=round(sum(s_bands) / len(s_bands), 1) if s_bands else None,
    )

    # Band trend (last 10 attempts with an overall_band, chronological order)
    trend_rows = [r for r in rows if r.Attempt.overall_band is not None][:10]
    band_trend = [
        BandTrendPoint(
            attempt_id=r.Attempt.id,
            band=r.Attempt.overall_band,
            date=r.Attempt.finished_at or r.Attempt.created_at,
        )
        for r in reversed(trend_rows)
    ]

    # Most recent in-progress attempt
    ip_stmt = (
        select(Attempt, Test.title, Test.test_number)
        .join(Test, Attempt.test_id == Test.id)
        .where(
            Attempt.user_id == actor.user_id,
            Attempt.mode == AttemptMode.FULL_MOCK.value,
            Attempt.status == AttemptStatus.IN_PROGRESS,
        )
        .order_by(Attempt.updated_at.desc())
        .limit(1)
    )
    ip_result = await db.execute(ip_stmt)
    ip_row = ip_result.first()

    in_progress = None
    if ip_row:
        att = ip_row.Attempt
        # Count answered questions for this attempt
        answered_count = (await db.execute(
            select(func.count(Answer.id))
            .where(Answer.attempt_id == att.id)
        )).scalar_one()
        # Count total questions across all sections of this test
        total_count = (await db.execute(
            select(func.count(Question.id))
            .join(Section, Question.section_id == Section.id)
            .where(Section.test_id == att.test_id)
        )).scalar_one()
        in_progress = InProgressAttempt(
            id=att.id,
            test_id=att.test_id,
            test_title=student_mock_label(slots.get(att.test_id)),
            answered=answered_count,
            total=total_count,
            updated_at=att.updated_at or att.created_at,
            section=await resume_section_for_attempt(db, att.id),
        )

    return DashboardResponse(
        tests_taken=len(rows),
        avg_band=round(sum(bands) / len(bands), 1) if bands else None,
        best_band=max(bands) if bands else None,
        section_bands=section_bands,
        band_trend=band_trend,
        in_progress=in_progress,
        recent=recent,
    )


@router.get("/tests", response_model=CatalogResponse)
async def student_tests(
    actor: Actor = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy.orm import selectinload

    tests_result = await db.execute(
        select(Test)
        .options(selectinload(Test.sections), selectinload(Test.section_settings))
        .where(Test.is_published == True)  # noqa: E712
        .order_by(Test.created_at.asc())
    )
    tests = list(tests_result.scalars().unique().all())

    if not tests:
        return CatalogResponse(groups=[])

    for t in tests:
        await settings_service.ensure_loaded(db, t)

    test_ids = [t.id for t in tests]

    # Best completed/scored attempt per test — fetch section bands
    best_attempts_stmt = (
        select(
            Attempt.test_id,
            func.max(Attempt.overall_band).label("overall_band"),
        )
        .where(
            Attempt.user_id == actor.user_id,
            Attempt.test_id.in_(test_ids),
            Attempt.mode == AttemptMode.FULL_MOCK.value,
            Attempt.status.in_([
                AttemptStatus.COMPLETED,
                AttemptStatus.AUTO_SCORED,
                AttemptStatus.FULLY_SCORED,
            ]),
        )
        .group_by(Attempt.test_id)
    )
    best_result = await db.execute(best_attempts_stmt)
    best_overall_by_test: dict[uuid.UUID, float | None] = {
        row.test_id: row.overall_band for row in best_result.all()
    }

    # One best attempt per test (highest overall, then latest) — avoids N+1.
    section_scores_by_test: dict[uuid.UUID, dict[str, float | None]] = {}
    if best_overall_by_test:
        best_rows = await db.execute(
            select(Attempt)
            .where(
                Attempt.user_id == actor.user_id,
                Attempt.test_id.in_(list(best_overall_by_test.keys())),
                Attempt.mode == AttemptMode.FULL_MOCK.value,
                Attempt.status.in_(
                    [
                        AttemptStatus.COMPLETED,
                        AttemptStatus.AUTO_SCORED,
                        AttemptStatus.FULLY_SCORED,
                    ]
                ),
                Attempt.overall_band.is_not(None),
            )
            .distinct(Attempt.test_id)
            .order_by(
                Attempt.test_id,
                Attempt.overall_band.desc(),
                Attempt.created_at.desc(),
            )
        )
        for attempt in best_rows.scalars().all():
            section_scores_by_test[attempt.test_id] = {
                "listening": attempt.listening_band,
                "reading": attempt.reading_band,
                "writing": attempt.writing_band,
                "speaking": attempt.speaking_band,
            }

    # In-progress attempt per test (full mock only — practice lives elsewhere)
    progress_stmt = (
        select(Attempt.test_id, Attempt.id)
        .where(
            Attempt.user_id == actor.user_id,
            Attempt.test_id.in_(test_ids),
            Attempt.mode == AttemptMode.FULL_MOCK.value,
            Attempt.status == AttemptStatus.IN_PROGRESS,
        )
    )
    progress_result = await db.execute(progress_stmt)
    in_progress_by_test: dict[uuid.UUID, uuid.UUID] = {
        row.test_id: row.id for row in progress_result.all()
    }

    # Last attempt date per test (full mock only — practice tracked separately)
    last_attempt_stmt = (
        select(Attempt.test_id, func.max(Attempt.created_at).label("last_at"))
        .where(
            Attempt.user_id == actor.user_id,
            Attempt.test_id.in_(test_ids),
            Attempt.mode == AttemptMode.FULL_MOCK.value,
        )
        .group_by(Attempt.test_id)
    )
    last_attempt_result = await db.execute(last_attempt_stmt)
    last_attempt_by_test = {row.test_id: row.last_at for row in last_attempt_result.all()}
    practice_indexes = await published_index_map(db)

    def _make_catalog_test(t: Test) -> CatalogTest:
        scores = section_scores_by_test.get(t.id, {})
        sections = {}
        for sec in ("listening", "reading", "writing", "speaking"):
            band = scores.get(sec)
            sections[sec] = SectionProgress(score=band, completed=band is not None)

        unique_types = {s.type for s in t.sections}
        duration = timed_total_minutes(t.section_settings)

        has_ip = t.id in in_progress_by_test
        has_score = t.id in best_overall_by_test
        test_status = "in_progress" if has_ip else ("completed" if has_score else "new")

        last_at = last_attempt_by_test.get(t.id)

        return CatalogTest(
            id=t.id,
            title=practice_set_label(practice_indexes.get(t.id)),
            book_name=None,
            test_type=t.type or "academic",
            duration_minutes=duration,
            section_count=len(unique_types),
            sections=sections,
            overall_score=best_overall_by_test.get(t.id),
            status=test_status,
            in_progress_attempt_id=in_progress_by_test.get(t.id),
            last_attempt_at=last_at.isoformat() if last_at else None,
        )

    return CatalogResponse(
        groups=[TestGroup(name="Practice", tests=[_make_catalog_test(t) for t in tests])]
    )


@router.get("/results")
async def student_results(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    actor: Actor = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Full-mock results list. Practice attempts are surfaced separately."""
    filters = [
        Attempt.user_id == actor.user_id,
        Attempt.mode == AttemptMode.FULL_MOCK.value,
    ]
    total = (
        await db.execute(select(func.count(Attempt.id)).where(*filters))
    ).scalar_one()

    stmt = (
        select(Attempt, Test.title, Test.test_number)
        .join(Test, Attempt.test_id == Test.id)
        .where(*filters)
        .order_by(Attempt.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    slots = await slot_map_for_user(db, actor.user_id)
    items = [
        {
            "id": str(r.Attempt.id),
            "test_id": str(r.Attempt.test_id),
            "test_title": student_mock_label(slots.get(r.Attempt.test_id)),
            "status": r.Attempt.status,
            "overall_band": r.Attempt.overall_band,
            "listening_band": r.Attempt.listening_band,
            "reading_band": r.Attempt.reading_band,
            "writing_band": r.Attempt.writing_band,
            "speaking_band": r.Attempt.speaking_band,
            "started_at": r.Attempt.started_at.isoformat() if r.Attempt.started_at else None,
            "finished_at": r.Attempt.finished_at.isoformat() if r.Attempt.finished_at else None,
            "created_at": r.Attempt.created_at.isoformat(),
        }
        for r in result.all()
    ]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/practice-results")
async def student_practice_results(
    actor: Actor = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Practice results (part + whole section) — kept separate from mock stats."""
    stmt = (
        select(Attempt, Test.title, Test.test_number)
        .join(Test, Attempt.test_id == Test.id)
        .where(
            Attempt.user_id == actor.user_id,
            Attempt.mode.in_(PRACTICE_MODES),
        )
        .order_by(Attempt.created_at.desc())
    )
    result = await db.execute(stmt)
    practice_indexes = await published_index_map(db)

    payload: list[dict] = []
    for r in result.all():
        att = r.Attempt
        section_type = att.practice_section_type
        mode = att.mode or AttemptMode.SINGLE_PART.value
        scope = "section" if mode == AttemptMode.SINGLE_SECTION.value else "part"
        payload.append(
            {
                "id": str(att.id),
                "test_id": str(att.test_id),
                "test_title": practice_set_label(practice_indexes.get(att.test_id)),
                "status": att.status,
                "mode": mode,
                "scope": scope,
                "section_type": section_type,
                "part_number": att.practice_part_number,
                "correct": att.practice_correct,
                "total": att.practice_total,
                "band": _practice_band_for(att, section_type),
                "started_at": att.started_at.isoformat() if att.started_at else None,
                "finished_at": att.finished_at.isoformat() if att.finished_at else None,
                "created_at": att.created_at.isoformat(),
            }
        )
    return payload


@router.get("/full-mock/status", response_model=FullMockStatus)
async def full_mock_status(
    actor: Actor = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    if actor.user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    live = await in_progress_full_mock(db, actor.user_id)
    title = None
    section = None
    if live is not None:
        slots = await slot_map_for_user(db, actor.user_id)
        title = student_mock_label(slots.get(live.test_id))
        section = await resume_section_for_attempt(db, live.id)
    published = await published_test_ids(db)
    return FullMockStatus(
        remaining=await remaining_count(db, actor.user_id),
        total_published=len(published),
        in_progress_attempt_id=live.id if live is not None else None,
        in_progress_test_id=live.test_id if live is not None else None,
        in_progress_title=title,
        in_progress_section=section,
    )


@router.post("/full-mock/start", response_model=AttemptRead)
async def start_full_mock(
    actor: Actor = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    if actor.user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        attempt = await start_next_full_mock(db, actor.user_id)
        return AttemptRead.model_validate(attempt)
    except NoUnusedMocks:
        raise http_no_mocks() from None
