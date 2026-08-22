import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import Numeric, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.answer import Answer
from app.models.attempt import Attempt, AttemptStatus
from app.models.evaluation_job import EvaluationJob, JobStatus
from app.models.question import Question
from app.models.section import Section
from app.models.section_progress import SectionProgress, SectionState
from app.models.test import Test
from app.models.user import User
from app.services.usage_quota import collect_usage
from app.utils.labels import format_test_label

router = APIRouter(
    prefix="/admin",
    tags=["Admin Panel"],
    dependencies=[Depends(get_current_admin)],
)


# ── Schemas ───────────────────────────────────────────────────────────────────


class StatPoint(BaseModel):
    attempts: int
    delta_vs_yesterday: int | None = None
    delta_percent: int | None = None


class DashboardStats(BaseModel):
    today: StatPoint
    week: StatPoint
    month: StatPoint


class DashboardAlert(BaseModel):
    type: str
    severity: str  # 'error' | 'warning'
    message: str
    action_url: str
    count: int


class ActivityPoint(BaseModel):
    date: str  # YYYY-MM-DD
    attempts_count: int


class InProgressItem(BaseModel):
    attempt_id: uuid.UUID
    student_name: str
    test_name: str
    current_section: str | None = None
    started_min_ago: int


class BandBucket(BaseModel):
    range: str
    count: int
    percentage: int


class BandDistribution(BaseModel):
    buckets: list[BandBucket]
    total_scored: int
    period_days: int = 30


class TopStudent(BaseModel):
    student_id: uuid.UUID
    name: str
    avg_band: float
    attempts_count: int


class PopularTest(BaseModel):
    test_id: uuid.UUID
    title: str
    attempts_count: int
    avg_band: float | None


class RecentActivityItem(BaseModel):
    type: str  # 'started' | 'finished' | 'submitted_writing'
    student_name: str
    test_name: str
    timestamp: datetime
    band: float | None = None
    attempt_id: uuid.UUID


class SkillStat(BaseModel):
    section: str  # 'listening' | 'reading' | 'writing' | 'speaking'
    avg_band: float | None
    count: int


class DashboardOverview(BaseModel):
    total_students: int
    active_students_week: int
    published_tests: int
    draft_tests: int
    completion_rate: int | None  # % of ended attempts that were completed (30d)
    avg_band: float | None  # overall avg band (30d)
    pending_evaluations: int  # AI jobs queued or processing


class AdminDashboardResponse(BaseModel):
    overview: DashboardOverview
    stats: DashboardStats
    alerts: list[DashboardAlert]
    activity_chart: list[ActivityPoint]
    in_progress: list[InProgressItem]
    band_distribution: BandDistribution
    skill_breakdown: list[SkillStat]
    top_students: list[TopStudent]
    popular_tests: list[PopularTest]
    recent_activity: list[RecentActivityItem]


# ── Endpoint ──────────────────────────────────────────────────────────────────


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def admin_dashboard(
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_start = today_start - timedelta(days=6)  # rolling 7-day window
    prev_week_start = week_start - timedelta(days=7)
    month_start = today_start - timedelta(days=29)  # rolling 30-day window
    prev_month_start = month_start - timedelta(days=30)

    # Single pass: all attempts created in the last 60 days.
    created_rows = (
        await db.execute(
            select(Attempt.created_at).where(Attempt.created_at >= prev_month_start)
        )
    ).scalars().all()

    def _count(start: datetime, end: datetime | None = None) -> int:
        return sum(
            1
            for c in created_rows
            if c is not None and c >= start and (end is None or c < end)
        )

    today_n = _count(today_start)
    yesterday_n = _count(yesterday_start, today_start)
    week_n = _count(week_start)
    prev_week_n = _count(prev_week_start, week_start)
    month_n = _count(month_start)
    prev_month_n = _count(prev_month_start, month_start)

    def _pct(current: int, previous: int) -> int | None:
        if previous == 0:
            return None
        return round((current - previous) / previous * 100)

    stats = DashboardStats(
        today=StatPoint(attempts=today_n, delta_vs_yesterday=today_n - yesterday_n),
        week=StatPoint(attempts=week_n, delta_percent=_pct(week_n, prev_week_n)),
        month=StatPoint(attempts=month_n, delta_percent=_pct(month_n, prev_month_n)),
    )

    # ── Activity chart: last 30 days, zero-filled ──
    buckets: dict[str, int] = {}
    for i in range(30):
        day = (month_start + timedelta(days=i)).date().isoformat()
        buckets[day] = 0
    for c in created_rows:
        if c is None or c < month_start:
            continue
        key = c.astimezone(timezone.utc).date().isoformat()
        if key in buckets:
            buckets[key] += 1
    activity_chart = [
        ActivityPoint(date=day, attempts_count=count) for day, count in buckets.items()
    ]

    # ── Alerts ──
    alerts: list[DashboardAlert] = []

    failed_n = (
        await db.execute(
            select(func.count(EvaluationJob.id)).where(
                EvaluationJob.status == JobStatus.FAILED
            )
        )
    ).scalar_one()
    if failed_n > 0:
        alerts.append(
            DashboardAlert(
                type="failed_scoring",
                severity="error",
                message=(
                    f"{failed_n} AI evaluation"
                    f"{'s' if failed_n != 1 else ''} failed"
                ),
                action_url="/results",
                count=failed_n,
            )
        )

    missing_key_n = (
        await db.execute(
            select(func.count(Question.id))
            .join(Section, Question.section_id == Section.id)
            .join(Test, Section.test_id == Test.id)
            .where(
                Test.is_published.is_(True),
                Question.answer_key.is_(None),
                Question.question_type.notin_(["essay", "speaking_part"]),
            )
        )
    ).scalar_one()
    if missing_key_n > 0:
        alerts.append(
            DashboardAlert(
                type="missing_answer_key",
                severity="warning",
                message=(
                    f"{missing_key_n} question"
                    f"{'s' if missing_key_n != 1 else ''} "
                    "in published tests have no answer key"
                ),
                action_url="/tests",
                count=missing_key_n,
            )
        )

    # ── In progress now ──
    ip_rows = (
        await db.execute(
            select(Attempt, User.full_name, Test.title, Test.test_number)
            .join(Test, Attempt.test_id == Test.id)
            .outerjoin(User, Attempt.user_id == User.id)
            .where(
                Attempt.status.in_(
                    [AttemptStatus.IN_PROGRESS, AttemptStatus.SPEAKING_IN_PROGRESS]
                )
            )
            .order_by(Attempt.started_at.desc().nullslast())
        )
    ).all()

    attempt_ids = [att.id for att, *_ in ip_rows]
    active_by_attempt: dict[uuid.UUID, str] = {}
    if attempt_ids:
        active_rows = (
            await db.execute(
                select(SectionProgress.attempt_id, SectionProgress.section_type)
                .where(
                    SectionProgress.attempt_id.in_(attempt_ids),
                    SectionProgress.state == SectionState.ACTIVE.value,
                )
            )
        ).all()
        active_by_attempt = {row.attempt_id: row.section_type for row in active_rows}

        # Fallback for legacy rows without section_progress: latest answered section.
        missing = [aid for aid in attempt_ids if aid not in active_by_attempt]
        if missing:
            latest_answer = (
                select(
                    Answer.attempt_id.label("attempt_id"),
                    Section.type.label("section_type"),
                    func.row_number()
                    .over(
                        partition_by=Answer.attempt_id,
                        order_by=Answer.updated_at.desc(),
                    )
                    .label("rn"),
                )
                .join(Question, Question.id == Answer.question_id)
                .join(Section, Section.id == Question.section_id)
                .where(Answer.attempt_id.in_(missing))
                .subquery()
            )
            fallback_rows = (
                await db.execute(
                    select(latest_answer.c.attempt_id, latest_answer.c.section_type).where(
                        latest_answer.c.rn == 1
                    )
                )
            ).all()
            for aid, section_type in fallback_rows:
                active_by_attempt[aid] = section_type

    in_progress: list[InProgressItem] = []
    for att, full_name, title, test_number in ip_rows:
        if att.status == AttemptStatus.SPEAKING_IN_PROGRESS:
            current_section = "speaking"
        else:
            current_section = active_by_attempt.get(att.id)

        started = att.started_at or att.created_at
        started_min_ago = 0
        if started is not None:
            delta = now - started.astimezone(timezone.utc)
            started_min_ago = max(0, int(delta.total_seconds() // 60))

        in_progress.append(
            InProgressItem(
                attempt_id=att.id,
                student_name=full_name or "Unknown",
                test_name=format_test_label(title, test_number),
                current_section=current_section,
                started_min_ago=started_min_ago,
            )
        )

    # ── Band distribution (last 30 days, scored only) ──
    scored_statuses = [
        AttemptStatus.AUTO_SCORED,
        AttemptStatus.FULLY_SCORED,
        AttemptStatus.COMPLETED_WITHOUT_SPEAKING,
    ]
    scored_rows = (
        await db.execute(
            select(Attempt.overall_band).where(
                Attempt.created_at >= month_start,
                Attempt.status.in_(scored_statuses),
                Attempt.overall_band.isnot(None),
                Attempt.overall_band > 0,
            )
        )
    ).scalars().all()

    band_bins = {"8-9": 0, "7-8": 0, "6-7": 0, "<6": 0}
    for b in scored_rows:
        if b >= 8:
            band_bins["8-9"] += 1
        elif b >= 7:
            band_bins["7-8"] += 1
        elif b >= 6:
            band_bins["6-7"] += 1
        else:
            band_bins["<6"] += 1

    total_scored = len(scored_rows)
    band_distribution = BandDistribution(
        buckets=[
            BandBucket(
                range=r,
                count=c,
                percentage=round(c / total_scored * 100) if total_scored else 0,
            )
            for r, c in band_bins.items()
        ],
        total_scored=total_scored,
    )

    # ── Skill breakdown: avg band per section (last 30 days) ──
    skill_cols = {
        "listening": Attempt.listening_band,
        "reading": Attempt.reading_band,
        "writing": Attempt.writing_band,
        "speaking": Attempt.speaking_band,
    }
    skill_stmt = select(
        *[
            expr
            for col in skill_cols.values()
            for expr in (
                func.avg(func.nullif(col, 0)),
                func.count(func.nullif(col, 0)),
            )
        ]
    ).where(
        Attempt.created_at >= month_start,
        Attempt.status.in_(scored_statuses),
    )
    skill_row = (await db.execute(skill_stmt)).one()
    skill_breakdown: list[SkillStat] = []
    for idx, section in enumerate(skill_cols):
        avg_val = skill_row[idx * 2]
        count_val = skill_row[idx * 2 + 1] or 0
        skill_breakdown.append(
            SkillStat(
                section=section,
                avg_band=round(float(avg_val), 1) if avg_val is not None else None,
                count=count_val,
            )
        )

    # ── Top students (top 5, min 3 attempts) ──
    top_stmt = (
        select(
            Attempt.user_id,
            User.full_name,
            func.round(cast(func.avg(Attempt.overall_band), Numeric), 1).label("avg_band"),
            func.count().label("cnt"),
        )
        .join(User, Attempt.user_id == User.id)
        .where(
            Attempt.created_at >= month_start,
            Attempt.status.in_(scored_statuses),
            Attempt.overall_band.isnot(None),
            Attempt.overall_band > 0,
            Attempt.user_id.isnot(None),
        )
        .group_by(Attempt.user_id, User.full_name)
        .having(func.count() >= 3)
        .order_by(func.avg(Attempt.overall_band).desc(), func.count().desc())
        .limit(5)
    )
    top_rows = (await db.execute(top_stmt)).all()
    top_students = [
        TopStudent(
            student_id=r.user_id,
            name=r.full_name or "Unknown",
            avg_band=float(r.avg_band),
            attempts_count=r.cnt,
        )
        for r in top_rows
    ]

    # ── Popular tests (top 5) ──
    pop_stmt = (
        select(
            Attempt.test_id,
            Test.title,
            Test.test_number,
            func.count().label("cnt"),
            func.avg(
                func.nullif(Attempt.overall_band, 0)
            ).label("avg_band"),
        )
        .join(Test, Attempt.test_id == Test.id)
        .where(Attempt.created_at >= month_start)
        .group_by(Attempt.test_id, Test.title, Test.test_number)
        .order_by(func.count().desc())
        .limit(5)
    )
    pop_rows = (await db.execute(pop_stmt)).all()
    popular_tests = [
        PopularTest(
            test_id=r.test_id,
            title=format_test_label(r.title, r.test_number),
            attempts_count=r.cnt,
            avg_band=round(float(r.avg_band), 1) if r.avg_band is not None else None,
        )
        for r in pop_rows
    ]

    # ── Recent activity (last 10 events) ──
    started_rows = (
        await db.execute(
            select(
                Attempt.id,
                Attempt.created_at,
                User.full_name,
                Test.title,
                Test.test_number,
            )
            .join(Test, Attempt.test_id == Test.id)
            .outerjoin(User, Attempt.user_id == User.id)
            .order_by(Attempt.created_at.desc())
            .limit(20)
        )
    ).all()

    finished_rows = (
        await db.execute(
            select(
                Attempt.id,
                Attempt.finished_at,
                Attempt.overall_band,
                User.full_name,
                Test.title,
                Test.test_number,
            )
            .join(Test, Attempt.test_id == Test.id)
            .outerjoin(User, Attempt.user_id == User.id)
            .where(Attempt.finished_at.isnot(None))
            .order_by(Attempt.finished_at.desc())
            .limit(20)
        )
    ).all()

    writing_rows = (
        await db.execute(
            select(
                Attempt.id,
                EvaluationJob.created_at,
                User.full_name,
                Test.title,
                Test.test_number,
            )
            .select_from(EvaluationJob)
            .join(Attempt, EvaluationJob.attempt_id == Attempt.id)
            .join(Test, Attempt.test_id == Test.id)
            .outerjoin(User, Attempt.user_id == User.id)
            .where(EvaluationJob.section_type == "writing")
            .order_by(EvaluationJob.created_at.desc())
            .limit(20)
        )
    ).all()

    events: list[RecentActivityItem] = []
    for r in started_rows:
        events.append(RecentActivityItem(
            type="started",
            student_name=r.full_name or "Unknown",
            test_name=format_test_label(r.title, r.test_number),
            timestamp=r.created_at,
            attempt_id=r.id,
        ))
    for r in finished_rows:
        events.append(RecentActivityItem(
            type="finished",
            student_name=r.full_name or "Unknown",
            test_name=format_test_label(r.title, r.test_number),
            timestamp=r.finished_at,
            band=r.overall_band if r.overall_band and r.overall_band > 0 else None,
            attempt_id=r.id,
        ))
    for r in writing_rows:
        events.append(RecentActivityItem(
            type="submitted_writing",
            student_name=r.full_name or "Unknown",
            test_name=format_test_label(r.title, r.test_number),
            timestamp=r.created_at,
            attempt_id=r.id,
        ))

    events.sort(key=lambda e: e.timestamp, reverse=True)
    recent_activity = events[:10]

    # ── Overview KPIs ──
    total_students = (
        await db.execute(
            select(func.count(User.id)).where(User.role == "student")
        )
    ).scalar_one()

    active_students_week = (
        await db.execute(
            select(func.count(func.distinct(Attempt.user_id))).where(
                Attempt.created_at >= week_start,
                Attempt.user_id.isnot(None),
            )
        )
    ).scalar_one()

    published_tests = (
        await db.execute(
            select(func.count(Test.id)).where(Test.is_published.is_(True))
        )
    ).scalar_one()
    draft_tests = (
        await db.execute(
            select(func.count(Test.id)).where(Test.is_published.is_(False))
        )
    ).scalar_one()

    pending_evaluations = (
        await db.execute(
            select(func.count(EvaluationJob.id)).where(
                EvaluationJob.status.in_([JobStatus.PENDING, JobStatus.PROCESSING])
            )
        )
    ).scalar_one()

    # Completion rate: of attempts that ended in the last 30 days, how many
    # were completed vs abandoned.
    completed_n = (
        await db.execute(
            select(func.count(Attempt.id)).where(
                Attempt.created_at >= month_start,
                Attempt.status.in_(
                    scored_statuses + [AttemptStatus.COMPLETED]
                ),
            )
        )
    ).scalar_one()
    abandoned_n = (
        await db.execute(
            select(func.count(Attempt.id)).where(
                Attempt.created_at >= month_start,
                Attempt.status == AttemptStatus.ABANDONED,
            )
        )
    ).scalar_one()
    ended_n = completed_n + abandoned_n
    completion_rate = round(completed_n / ended_n * 100) if ended_n else None

    avg_band = (
        round(sum(scored_rows) / len(scored_rows), 1) if scored_rows else None
    )

    overview = DashboardOverview(
        total_students=total_students,
        active_students_week=active_students_week,
        published_tests=published_tests,
        draft_tests=draft_tests,
        completion_rate=completion_rate,
        avg_band=avg_band,
        pending_evaluations=pending_evaluations,
    )

    return AdminDashboardResponse(
        overview=overview,
        stats=stats,
        alerts=alerts,
        activity_chart=activity_chart,
        in_progress=in_progress,
        band_distribution=band_distribution,
        skill_breakdown=skill_breakdown,
        top_students=top_students,
        popular_tests=popular_tests,
        recent_activity=recent_activity,
    )


# ── Analytics schemas ─────────────────────────────────────────────────────────


class AnalyticsSummary(BaseModel):
    total_attempts: int
    completed_attempts: int
    completion_rate: int | None
    avg_band: float | None
    active_students: int


class BandTrendPoint(BaseModel):
    bucket: str  # YYYY-MM-DD
    count: int
    overall: float | None = None
    listening: float | None = None
    reading: float | None = None
    writing: float | None = None
    speaking: float | None = None


class AnalyticsSectionAverage(BaseModel):
    section: str
    avg_band: float | None
    count: int


class TestDifficulty(BaseModel):
    test_id: uuid.UUID
    title: str
    attempts_count: int
    avg_band: float | None
    completion_rate: int | None


class GroupComparison(BaseModel):
    group_name: str
    students: int
    attempts_count: int
    avg_band: float | None


class CompletionBreakdown(BaseModel):
    completed: int
    abandoned: int
    in_progress: int


class AnalyticsResponse(BaseModel):
    period_days: int
    summary: AnalyticsSummary
    band_trend: list[BandTrendPoint]
    section_averages: list[AnalyticsSectionAverage]
    test_difficulty: list[TestDifficulty]
    group_comparison: list[GroupComparison]
    completion: CompletionBreakdown


# ── Analytics endpoint ────────────────────────────────────────────────────────


@router.get("/analytics", response_model=AnalyticsResponse)
async def admin_analytics(
    db: AsyncSession = Depends(get_db),
    days: int = Query(30),
):
    if days not in (7, 30, 90):
        days = 30

    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
        days=days - 1
    )

    scored_set = [
        AttemptStatus.AUTO_SCORED,
        AttemptStatus.FULLY_SCORED,
        AttemptStatus.COMPLETED_WITHOUT_SPEAKING,
    ]

    # ── Fetch attempts in window once ──
    rows = (
        await db.execute(
            select(
                Attempt.created_at,
                Attempt.status,
                Attempt.overall_band,
                Attempt.listening_band,
                Attempt.reading_band,
                Attempt.writing_band,
                Attempt.speaking_band,
                Attempt.user_id,
                Attempt.test_id,
            ).where(Attempt.created_at >= start)
        )
    ).all()

    # ── Summary ──
    total_attempts = len(rows)
    completed_statuses = {s.value for s in scored_set} | {AttemptStatus.COMPLETED.value}
    abandoned_val = AttemptStatus.ABANDONED.value
    ip_vals = {AttemptStatus.IN_PROGRESS.value, AttemptStatus.SPEAKING_IN_PROGRESS.value}

    completed_n = sum(1 for r in rows if r.status in completed_statuses)
    abandoned_n = sum(1 for r in rows if r.status == abandoned_val)
    ip_n = sum(1 for r in rows if r.status in ip_vals)

    ended = completed_n + abandoned_n
    completion_rate = round(completed_n / ended * 100) if ended else None

    scored_bands = [
        r.overall_band
        for r in rows
        if r.status in {s.value for s in scored_set}
        and r.overall_band is not None
        and r.overall_band > 0
    ]
    avg_band = round(sum(scored_bands) / len(scored_bands), 1) if scored_bands else None

    active_students = len({r.user_id for r in rows if r.user_id is not None})

    summary = AnalyticsSummary(
        total_attempts=total_attempts,
        completed_attempts=completed_n,
        completion_rate=completion_rate,
        avg_band=avg_band,
        active_students=active_students,
    )

    # ── Band trend (bucketed) ──
    def _bucket_key(dt: datetime) -> str:
        d = dt.astimezone(timezone.utc).date()
        if days == 90:
            # Weekly: Monday of that week
            monday = d - timedelta(days=d.weekday())
            return monday.isoformat()
        return d.isoformat()

    # Build empty buckets
    trend_buckets: dict[str, list] = {}
    if days == 90:
        cursor = start.date() - timedelta(days=start.date().weekday())
        end_date = now.date()
        while cursor <= end_date:
            trend_buckets[cursor.isoformat()] = []
            cursor += timedelta(days=7)
    else:
        for i in range(days):
            d = (start + timedelta(days=i)).date().isoformat()
            trend_buckets[d] = []

    scored_vals = {s.value for s in scored_set}
    for r in rows:
        if r.status not in scored_vals:
            continue
        if r.overall_band is None or r.overall_band <= 0:
            continue
        key = _bucket_key(r.created_at)
        if key in trend_buckets:
            trend_buckets[key].append(r)

    def _safe_avg(vals: list[float | None]) -> float | None:
        clean = [v for v in vals if v is not None and v > 0]
        return round(sum(clean) / len(clean), 1) if clean else None

    band_trend = [
        BandTrendPoint(
            bucket=bk,
            count=len(items),
            overall=_safe_avg([r.overall_band for r in items]),
            listening=_safe_avg([r.listening_band for r in items]),
            reading=_safe_avg([r.reading_band for r in items]),
            writing=_safe_avg([r.writing_band for r in items]),
            speaking=_safe_avg([r.speaking_band for r in items]),
        )
        for bk, items in trend_buckets.items()
    ]

    # ── Section averages ──
    section_cols = {
        "listening": "listening_band",
        "reading": "reading_band",
        "writing": "writing_band",
        "speaking": "speaking_band",
    }
    section_averages_out: list[AnalyticsSectionAverage] = []
    for sec_name, attr in section_cols.items():
        vals = [
            getattr(r, attr)
            for r in rows
            if r.status in scored_vals
            and getattr(r, attr) is not None
            and getattr(r, attr) > 0
        ]
        section_averages_out.append(
            AnalyticsSectionAverage(
                section=sec_name,
                avg_band=round(sum(vals) / len(vals), 1) if vals else None,
                count=len(vals),
            )
        )

    # ── Test difficulty (SQL, top 10 hardest) ──
    td_completed = scored_set + [AttemptStatus.COMPLETED]
    td_stmt = (
        select(
            Attempt.test_id,
            Test.title,
            Test.test_number,
            func.count().label("cnt"),
            func.round(
                cast(func.avg(func.nullif(Attempt.overall_band, 0)), Numeric), 1
            ).label("avg_band"),
            func.count()
            .filter(Attempt.status.in_(td_completed))
            .label("completed_cnt"),
            func.count()
            .filter(Attempt.status == AttemptStatus.ABANDONED)
            .label("abandoned_cnt"),
        )
        .join(Test, Attempt.test_id == Test.id)
        .where(Attempt.created_at >= start)
        .group_by(Attempt.test_id, Test.title, Test.test_number)
        .having(
            func.count().filter(Attempt.status.in_(scored_set)) >= 1
        )
        .order_by(func.avg(func.nullif(Attempt.overall_band, 0)).asc().nullslast())
        .limit(10)
    )
    td_rows = (await db.execute(td_stmt)).all()
    test_difficulty = []
    for r in td_rows:
        td_ended = (r.completed_cnt or 0) + (r.abandoned_cnt or 0)
        test_difficulty.append(
            TestDifficulty(
                test_id=r.test_id,
                title=format_test_label(r.title, r.test_number),
                attempts_count=r.cnt,
                avg_band=float(r.avg_band) if r.avg_band is not None else None,
                completion_rate=round(r.completed_cnt / td_ended * 100)
                if td_ended
                else None,
            )
        )

    # ── Group comparison ──
    grp_label = func.coalesce(User.group_name, "No group").label("grp")
    gc_stmt = (
        select(
            grp_label,
            func.count(func.distinct(Attempt.user_id)).label("students"),
            func.count().label("cnt"),
            func.round(
                cast(func.avg(func.nullif(Attempt.overall_band, 0)), Numeric), 1
            ).label("avg_band"),
        )
        .join(User, Attempt.user_id == User.id)
        .where(
            Attempt.created_at >= start,
            Attempt.user_id.isnot(None),
        )
        .group_by(User.group_name)
        .order_by(func.avg(func.nullif(Attempt.overall_band, 0)).desc().nullslast())
    )
    gc_rows = (await db.execute(gc_stmt)).all()
    group_comparison = [
        GroupComparison(
            group_name=r.grp,
            students=r.students,
            attempts_count=r.cnt,
            avg_band=float(r.avg_band) if r.avg_band is not None else None,
        )
        for r in gc_rows
    ]

    # ── Completion breakdown ──
    completion = CompletionBreakdown(
        completed=completed_n,
        abandoned=abandoned_n,
        in_progress=ip_n,
    )

    return AnalyticsResponse(
        period_days=days,
        summary=summary,
        band_trend=band_trend,
        section_averages=section_averages_out,
        test_difficulty=test_difficulty,
        group_comparison=group_comparison,
        completion=completion,
    )


@router.get("/usage")
async def get_usage():
    """Remaining quota and spend per external provider.

    Shapes vary per provider because each exposes a different amount, so the
    tiles are returned as loose dicts rather than one rigid schema.
    """
    return await collect_usage()

