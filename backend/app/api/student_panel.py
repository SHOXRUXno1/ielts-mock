import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Actor, get_current_student
from app.core.database import get_db
from app.models.attempt import Attempt, AttemptStatus
from app.models.test import Test

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


class DashboardResponse(BaseModel):
    tests_taken: int
    avg_band: float | None
    best_band: float | None
    recent: list[DashboardAttempt]


# ── Catalog schemas ───────────────────────────────────────────────────────────

class SectionProgress(BaseModel):
    score: float | None
    completed: bool


class CatalogTest(BaseModel):
    id: uuid.UUID
    title: str
    sections: dict[str, SectionProgress]
    overall_score: float | None
    in_progress_attempt_id: uuid.UUID | None = None


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


@router.get("/dashboard", response_model=DashboardResponse)
async def student_dashboard(
    actor: Actor = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    # All finished attempts for this student
    stmt = (
        select(Attempt, Test.title)
        .join(Test, Attempt.test_id == Test.id)
        .where(
            Attempt.user_id == actor.user_id,
            Attempt.status.in_([AttemptStatus.COMPLETED, AttemptStatus.SCORED]),
        )
        .order_by(Attempt.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    bands = [r.Attempt.overall_band for r in rows if r.Attempt.overall_band is not None]
    recent = [
        DashboardAttempt(
            id=r.Attempt.id,
            test_id=r.Attempt.test_id,
            test_title=r.title,
            overall_band=r.Attempt.overall_band,
            status=r.Attempt.status,
            finished_at=r.Attempt.finished_at,
            created_at=r.Attempt.created_at,
        )
        for r in rows[:5]
    ]

    return DashboardResponse(
        tests_taken=len(rows),
        avg_band=round(sum(bands) / len(bands), 1) if bands else None,
        best_band=max(bands) if bands else None,
        recent=recent,
    )


@router.get("/tests", response_model=CatalogResponse)
async def student_tests(
    actor: Actor = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    tests_result = await db.execute(
        select(Test).where(Test.is_published == True).order_by(Test.created_at.asc())  # noqa: E712
    )
    tests = tests_result.scalars().all()

    if not tests:
        return CatalogResponse(groups=[])

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
            Attempt.status.in_([AttemptStatus.COMPLETED, AttemptStatus.SCORED]),
        )
        .group_by(Attempt.test_id)
    )
    best_result = await db.execute(best_attempts_stmt)
    best_overall_by_test: dict[uuid.UUID, float | None] = {
        row.test_id: row.overall_band for row in best_result.all()
    }

    # For section-level scores, fetch the single best attempt per test
    section_scores_by_test: dict[uuid.UUID, dict[str, float | None]] = {}
    for test_id, overall in best_overall_by_test.items():
        if overall is None:
            continue
        attempt_row = await db.execute(
            select(Attempt)
            .where(
                Attempt.user_id == actor.user_id,
                Attempt.test_id == test_id,
                Attempt.status.in_([AttemptStatus.COMPLETED, AttemptStatus.SCORED]),
                Attempt.overall_band == overall,
            )
            .limit(1)
        )
        attempt = attempt_row.scalar_one_or_none()
        if attempt:
            section_scores_by_test[test_id] = {
                "listening": attempt.listening_band,
                "reading": attempt.reading_band,
                "writing": attempt.writing_band,
                "speaking": attempt.speaking_band,
            }

    # In-progress attempt per test
    progress_stmt = (
        select(Attempt.test_id, Attempt.id)
        .where(
            Attempt.user_id == actor.user_id,
            Attempt.test_id.in_(test_ids),
            Attempt.status == AttemptStatus.IN_PROGRESS,
        )
    )
    progress_result = await db.execute(progress_stmt)
    in_progress_by_test: dict[uuid.UUID, uuid.UUID] = {
        row.test_id: row.id for row in progress_result.all()
    }

    # Build catalog tests
    def _make_catalog_test(t: Test) -> CatalogTest:
        scores = section_scores_by_test.get(t.id, {})
        sections = {}
        for sec in ("listening", "reading", "writing", "speaking"):
            band = scores.get(sec)
            sections[sec] = SectionProgress(score=band, completed=band is not None)
        return CatalogTest(
            id=t.id,
            title=t.title,
            sections=sections,
            overall_score=best_overall_by_test.get(t.id),
            in_progress_attempt_id=in_progress_by_test.get(t.id),
        )

    # Group by book_name (preserve insertion order; unknown → "Other")
    groups_map: dict[str, list[CatalogTest]] = {}
    for t in tests:
        group_name = t.book_name or "Other"
        groups_map.setdefault(group_name, []).append(_make_catalog_test(t))

    return CatalogResponse(
        groups=[TestGroup(name=name, tests=items) for name, items in groups_map.items()]
    )


@router.get("/results")
async def student_results(
    actor: Actor = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Attempt, Test.title)
        .join(Test, Attempt.test_id == Test.id)
        .where(Attempt.user_id == actor.user_id)
        .order_by(Attempt.created_at.desc())
    )
    result = await db.execute(stmt)
    return [
        {
            "id": str(r.Attempt.id),
            "test_id": str(r.Attempt.test_id),
            "test_title": r.title,
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
