import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import Actor, get_current_actor
from app.core.database import get_db
from app.models.answer import Answer
from app.models.attempt import Attempt, AttemptMode, AttemptStatus, PRACTICE_MODES
from app.models.evaluation_job import EvaluationJob, JobStatus
from app.models.question import Question
from app.models.section import Section, SectionType
from app.models.section_progress import SectionProgress, SectionState
from app.models.test import Test
from app.schemas.attempt import (
    AnswersBulkSubmit,
    AnswerSubmit,
    AttemptDetailRead,
    AttemptProgressRead,
    AttemptRead,
    EnterSectionResponse,
    SealSectionRequest,
    SealSectionResponse,
    SectionProgressRead,
)
from app.services.band_calc import compute_overall_band, derive_scored_status
from app.services.scoring import (
    correct_to_listening_band,
    correct_to_reading_band,
    score_section,
)
from app.services import section_progress as sp
from app.services import section_settings as settings_service
from app.services.student_mock import in_progress_full_mock

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Attempts"])

_VALID_SECTION_TYPES = {t.value for t in SectionType}


def _section_type_str(section_type: SectionType | str) -> str:
    return section_type.value if isinstance(section_type, SectionType) else section_type


def _assert_attempt_access(attempt: Attempt, actor: Actor) -> None:
    """Students can only access their own attempts."""
    if actor.role == "student" and attempt.user_id != actor.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _progress_read(row: SectionProgress) -> SectionProgressRead:
    return SectionProgressRead(
        section_type=row.section_type,
        state=row.state if isinstance(row.state, str) else row.state.value,
        started_at=row.started_at,
        ends_at=row.ends_at,
        sealed_at=row.sealed_at,
        sealed_reason=row.sealed_reason,
    )


async def _load_attempt_or_404(
    db: AsyncSession,
    attempt_id: uuid.UUID,
    actor: Actor,
) -> Attempt:
    attempt = await db.get(Attempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    _assert_attempt_access(attempt, actor)
    return attempt


async def _load_progress_rows(
    db: AsyncSession,
    attempt_id: uuid.UUID,
    *,
    for_update: bool = False,
) -> list[SectionProgress]:
    stmt = select(SectionProgress).where(SectionProgress.attempt_id == attempt_id)
    if for_update:
        stmt = stmt.with_for_update()
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _load_test_sections(
    db: AsyncSession,
    test_id: uuid.UUID,
) -> list[Section]:
    result = await db.execute(select(Section).where(Section.test_id == test_id))
    return list(result.scalars().all())


async def _upsert_answers(
    db: AsyncSession,
    attempt_id: uuid.UUID,
    answers: list[AnswerSubmit],
) -> int:
    """Idempotent upsert — safe under concurrent autosave via ON CONFLICT."""
    if not answers:
        return 0
    # Last write wins if the same question_id appears twice in one payload.
    by_qid: dict[uuid.UUID, AnswerSubmit] = {}
    for item in answers:
        by_qid[item.question_id] = item

    rows = [
        {
            "id": uuid.uuid4(),
            "attempt_id": attempt_id,
            "question_id": item.question_id,
            "response": item.response,
        }
        for item in by_qid.values()
    ]
    stmt = pg_insert(Answer).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["attempt_id", "question_id"],
        set_={"response": stmt.excluded.response},
    )
    await db.execute(stmt)
    return len(by_qid)


async def _activate_missing_progress(
    db: AsyncSession,
    attempt: Attempt,
    section_type: str,
    now: datetime,
) -> SectionProgress:
    """Back-compat: create a missing progress row as ACTIVE with defaults."""
    logger.warning(
        "Missing SectionProgress for attempt=%s section=%s on answer submit. "
        "Auto-creating as ACTIVE.",
        attempt.id,
        section_type,
    )
    settings = await settings_service.ensure_settings(db, attempt.test_id)
    row = SectionProgress(
        attempt_id=attempt.id,
        section_type=section_type,
        state=SectionState.ACTIVE.value,
        started_at=now,
        ends_at=sp.compute_ends_at(now, settings, section_type),
    )
    db.add(row)
    await db.flush()
    return row


def _present_types_from_sections(sections: list[Section]) -> list[str]:
    found = {_section_type_str(s.type) for s in sections}
    return [t for t in sp.TYPE_ORDER if t in found]


def _present_types_for_attempt(
    attempt: Attempt,
    sections: list[Section],
) -> list[str]:
    """Section-order gate for this attempt.

    Full mock: every type present in the test. Practice: only the targeted
    type — the sequential L→R→W→S rule doesn't apply when the student picks
    a part or a whole section.
    """
    mode = getattr(attempt, "mode", None) or AttemptMode.FULL_MOCK.value
    if mode in PRACTICE_MODES:
        target = _resolve_practice_section_type(attempt)
        if target is not None:
            return [target]
    return _present_types_from_sections(sections)


async def _raise_section_expired(
    db: AsyncSession,
    rows: list[SectionProgress],
    row: SectionProgress,
    now: datetime,
    *,
    present_types: list[str] | None = None,
) -> None:
    """Seal with TIMEOUT and raise structured 409 SECTION_EXPIRED."""
    if row.section_type == SectionType.SPEAKING.value:
        logger.warning(
            "Speaking session exceeded safety cap attempt=%s ends_at=%s now=%s",
            row.attempt_id,
            row.ends_at,
            now,
        )
    sp.apply_timeout_seal(row, now)
    await db.commit()
    nxt = sp.next_not_started_type(rows, present_types)
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=sp.expired_detail(row, nxt),
    )


async def _enforce_section_writable(
    db: AsyncSession,
    attempt: Attempt,
    question_ids: list[uuid.UUID],
    now: datetime,
) -> None:
    """Reject answers for sealed / expired / not-started sections.

    Locks progress rows (FOR UPDATE) so concurrent late submits race safely:
    only one request seals; the rest see SEALED.
    """
    if not question_ids:
        return

    q_result = await db.execute(
        select(Question.id, Section.type)
        .join(Section, Section.id == Question.section_id)
        .where(Question.id.in_(question_ids))
    )
    q_types: dict[uuid.UUID, str] = {}
    for qid, stype in q_result.all():
        q_types[qid] = _section_type_str(stype)

    missing = [qid for qid in question_ids if qid not in q_types]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown question in payload",
        )

    affected_types = {q_types[qid] for qid in question_ids}
    # Lock existing rows only — do not silently create NOT_STARTED here.
    # A truly missing row (pre-Phase-1 edge case) is healed as ACTIVE below.
    rows = await _load_progress_rows(db, attempt.id, for_update=True)
    by_type = {r.section_type: r for r in rows}

    for stype in affected_types:
        row = by_type.get(stype)
        if row is None:
            row = await _activate_missing_progress(db, attempt, stype, now)
            rows.append(row)
            by_type[stype] = row

        state = row.state if isinstance(row.state, str) else row.state.value
        if state == SectionState.SEALED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Section already completed",
            )
        if state == SectionState.NOT_STARTED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Section not started",
            )
        if state == SectionState.ACTIVE.value and sp.is_expired(row, now):
            sections = await _load_test_sections(db, attempt.test_id)
            present = _present_types_from_sections(sections)
            await _raise_section_expired(
                db, rows, row, now, present_types=present
            )


def _attempt_progress_types(attempt: Attempt) -> tuple[str, ...]:
    """Section types this attempt should carry progress rows for.

    Full-mock attempts always seed the canonical four types. Practice
    attempts scope to just the targeted section type.
    """
    mode = getattr(attempt, "mode", None) or AttemptMode.FULL_MOCK.value
    if mode in PRACTICE_MODES:
        target = _resolve_practice_section_type(attempt)
        if target is not None:
            return (target,)
    return sp.TYPE_ORDER


def _resolve_practice_section_type(attempt: Attempt) -> str | None:
    """Target skill for a practice attempt.

    Prefers the denormalized ``practice_section_type`` column (works for both
    single_part and single_section). Falls back to the cached Section row.
    """
    stype = getattr(attempt, "practice_section_type", None)
    if stype:
        return stype
    section = getattr(attempt, "_practice_section_cache", None)
    if section is not None:
        return _section_type_str(section.type)
    return None


async def _practice_duration_override(
    db: AsyncSession,
    attempt: Attempt,
    section_type: str,
) -> int | None:
    """Per-part duration for a practice enter, or None (fall back to section).

    Whole-section practice always returns None so ``compute_ends_at`` uses
    ``TestSectionSettings`` for the full skill budget.
    """
    from app.services import practice_parts

    mode = getattr(attempt, "mode", None) or AttemptMode.FULL_MOCK.value
    if mode == AttemptMode.SINGLE_SECTION.value:
        return None
    if mode != AttemptMode.SINGLE_PART.value:
        return None
    section = await _load_practice_section(db, attempt)
    if section is None or attempt.practice_part_number is None:
        return None
    if _section_type_str(section.type) != section_type:
        return None
    # part_count derived from siblings of the same type (for proportional default)
    result = await db.execute(
        select(Section).where(
            Section.test_id == attempt.test_id,
            Section.type == section.type,
        )
    )
    siblings = list(result.scalars().all())
    part_count = len(siblings) or 1
    return await practice_parts.resolve_duration_minutes(
        db,
        attempt.test_id,
        section_type,
        attempt.practice_part_number,
        part_count=part_count,
    )


async def _load_practice_section(
    db: AsyncSession,
    attempt: Attempt,
) -> Section | None:
    """Load and cache the practice section on the attempt (idempotent)."""
    cached = getattr(attempt, "_practice_section_cache", None)
    if cached is not None:
        return cached
    if attempt.practice_section_id is None:
        return None
    section = await db.get(Section, attempt.practice_section_id)
    if section is not None:
        attempt._practice_section_cache = section
    return section


async def _ensure_progress_rows_for_attempt(
    db: AsyncSession,
    attempt: Attempt,
    *,
    for_update: bool = False,
) -> list[SectionProgress]:
    """Create missing SectionProgress rows for the attempt's mode-scoped types."""
    existing = await _load_progress_rows(db, attempt.id, for_update=for_update)
    types = await _resolve_progress_types(db, attempt)
    existing_types = {r.section_type for r in existing}
    missing_types = [t for t in types if t not in existing_types]
    if missing_types:
        for row in sp.ensure_progress_rows(attempt.id, present_types=missing_types):
            db.add(row)
            existing.append(row)
        await db.flush()
        if for_update:
            existing = await _load_progress_rows(
                db, attempt.id, for_update=True
            )
    return existing


def _writing_task_key(q: Question) -> str | None:
    tn = q.task_number if q.task_number in (1, 2) else (
        q.order if q.order in (1, 2) else None
    )
    return f"task_{tn}" if tn is not None else None


async def _enqueue_writing_job(
    db: AsyncSession,
    attempt: Attempt,
    questions: list[Question],
    answers: list[Answer],
    *,
    practice: bool,
    practice_task_number: int | None = None,
) -> int:
    """Build and enqueue a writing EvaluationJob. Returns number of tasks."""
    writing_answers: dict[str, str] = {}
    for a in answers:
        for q in questions:
            if q.id != a.question_id:
                continue
            key = _writing_task_key(q)
            if not key:
                continue
            text = a.response.get("answer", "") if isinstance(a.response, dict) else ""
            if isinstance(text, str):
                writing_answers[key] = text

    # Drop empty answers so we don't score blank tasks.
    writing_answers = {k: v for k, v in writing_answers.items() if v.strip()}
    if not writing_answers:
        return 0

    prompts: dict[str, str] = {}
    task_statements: dict[str, str] = {}
    task_questions: dict[str, str] = {}
    task_descriptions: dict[str, str] = {}
    task_instructions: dict[str, str] = {}
    images: dict[str, str] = {}
    essay_types: dict[str, str] = {}
    for q in questions:
        key = _writing_task_key(q)
        if not key or key not in writing_answers:
            continue
        content = q.content if isinstance(q.content, dict) else {}
        stmt = content.get("task_statement") or ""
        qn = content.get("task_question") or ""
        desc = content.get("task_description") or content.get("prompt", "")
        instr = content.get("task_instruction") or ""
        prompts[key] = f"{desc}\n\n{instr}".strip() if instr else desc
        task_statements[key] = stmt or desc
        task_questions[key] = qn
        task_descriptions[key] = desc
        task_instructions[key] = instr
        img = q.image_url or content.get("image_url")
        if img:
            images[key] = img
        et = getattr(q, "essay_type", None)
        if et:
            essay_types[key] = et

    input_data: dict = {
        "type": "writing",
        "answers": writing_answers,
        "prompts": prompts,
        "task_statements": task_statements,
        "task_questions": task_questions,
        "task_descriptions": task_descriptions,
        "task_instructions": task_instructions,
        "images": images,
        "essay_types": essay_types,
        "practice": practice,
    }
    if practice_task_number is not None:
        input_data["practice_task_number"] = practice_task_number

    db.add(
        EvaluationJob(
            attempt_id=attempt.id,
            section_type="writing",
            status=JobStatus.PENDING,
            input_data=input_data,
        )
    )
    return len(writing_answers)


async def _finish_practice_attempt(
    db: AsyncSession,
    attempt: Attempt,
) -> Attempt:
    """Practice finish path (single_part or single_section).

    * single_part L/R: score one Section; raw only, no band.
    * single_section L/R: aggregate all Sections of the type; write band + raw.
    * Writing single_part: one essay eval job.
    * Writing single_section: both essays, weighted band via worker.
    * Speaking: SpeakingSession bridge scores via /speaking-score.
    """
    now = datetime.now(timezone.utc)
    attempt.status = AttemptStatus.COMPLETED
    attempt.finished_at = now

    rows = await _load_progress_rows(db, attempt.id)
    for row in rows:
        state = row.state if isinstance(row.state, str) else row.state.value
        if state != SectionState.SEALED.value:
            sp.apply_seal(row, sp.SEAL_REASON_SUBMIT, now)

    stype = _resolve_practice_section_type(attempt)
    if stype is None:
        # Last-resort: load via practice_section_id for legacy rows.
        section = await _load_practice_section(db, attempt)
        if section is not None:
            stype = _section_type_str(section.type)
    if stype is None:
        await db.commit()
        stmt = (
            select(Attempt)
            .options(selectinload(Attempt.evaluation_jobs))
            .where(Attempt.id == attempt.id)
        )
        return (await db.execute(stmt)).scalar_one()

    is_whole_section = (
        (attempt.mode or "") == AttemptMode.SINGLE_SECTION.value
    )

    if is_whole_section:
        # All sibling sections of the target skill.
        sec_result = await db.execute(
            select(Section)
            .options(selectinload(Section.questions))
            .where(
                Section.test_id == attempt.test_id,
                Section.type == stype,
            )
            .order_by(Section.order)
        )
        sections = list(sec_result.scalars().all())
        questions = [q for s in sections for q in (s.questions or [])]
    else:
        section = await _load_practice_section(db, attempt)
        if section is None:
            await db.commit()
            stmt = (
                select(Attempt)
                .options(selectinload(Attempt.evaluation_jobs))
                .where(Attempt.id == attempt.id)
            )
            return (await db.execute(stmt)).scalar_one()
        q_result = await db.execute(
            select(Question).where(Question.section_id == section.id)
        )
        questions = list(q_result.scalars().all())
        sections = [section]

    q_ids = [q.id for q in questions]
    a_result = await db.execute(
        select(Answer).where(
            Answer.attempt_id == attempt.id,
            Answer.question_id.in_(q_ids) if q_ids else Answer.question_id.is_(None),
        )
    )
    answers = list(a_result.scalars().all())
    part_number = attempt.practice_part_number or 1

    if stype in ("listening", "reading"):
        if is_whole_section:
            correct = 0
            total = 0
            for section in sections:
                sec_qs = list(section.questions or [])
                sec_ans = [
                    a for a in answers
                    if any(q.id == a.question_id for q in sec_qs)
                ]
                c, t = score_section(sec_qs, sec_ans)
                correct += c
                total += t
            attempt.practice_correct = correct
            attempt.practice_total = total
            if stype == "listening":
                attempt.listening_band = correct_to_listening_band(correct)
                attempt.listening_raw = correct
            else:
                attempt.reading_band = correct_to_reading_band(correct)
                attempt.reading_raw = correct
        else:
            correct, total = score_section(questions, answers)
            attempt.practice_correct = correct
            attempt.practice_total = total
        attempt.status = AttemptStatus.AUTO_SCORED
    elif stype == "writing":
        if is_whole_section:
            task_count = await _enqueue_writing_job(
                db, attempt, questions, answers, practice=True
            )
            attempt.practice_total = task_count or 2
            attempt.practice_correct = None
        else:
            target_questions = [
                q for q in questions
                if (q.task_number or q.order) == part_number
            ]
            await _enqueue_writing_job(
                db,
                attempt,
                target_questions,
                answers,
                practice=True,
                practice_task_number=part_number,
            )
            attempt.practice_total = 1
            attempt.practice_correct = None
    else:
        # Speaking practice — SpeakingSession bridge scores it separately.
        pass

    await db.commit()
    stmt = (
        select(Attempt)
        .options(selectinload(Attempt.evaluation_jobs))
        .where(Attempt.id == attempt.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def _resolve_progress_types(
    db: AsyncSession,
    attempt: Attempt,
) -> tuple[str, ...]:
    """Resolve mode-scoped types, loading the practice section if needed."""
    mode = getattr(attempt, "mode", None) or AttemptMode.FULL_MOCK.value
    if mode not in PRACTICE_MODES:
        return sp.TYPE_ORDER
    target = _resolve_practice_section_type(attempt)
    if target is not None:
        return (target,)
    # Legacy single_part rows may lack practice_section_type — load via FK.
    if mode == AttemptMode.SINGLE_PART.value:
        section = await _load_practice_section(db, attempt)
        if section is not None:
            return (_section_type_str(section.type),)
    return sp.TYPE_ORDER


@router.get("/tests/{test_id}/attempts/current", response_model=AttemptRead)
async def get_current_attempt(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """Return the caller's in-progress attempt for this test, or 404.

    Does not create a new attempt — used for deep-link auto-resume.
    """
    test = await db.get(Test, test_id)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    if actor.role == "student" and not test.is_published:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Test not available")

    if actor.user_id is None:
        # .env admin has no user_id — no durable in-progress attempt to resume
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No in-progress attempt")

    result = await db.execute(
        select(Attempt).where(
            Attempt.user_id == actor.user_id,
            Attempt.test_id == test_id,
            Attempt.status == AttemptStatus.IN_PROGRESS,
            Attempt.mode == AttemptMode.FULL_MOCK.value,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No in-progress attempt")
    return existing


@router.post("/tests/{test_id}/attempts", response_model=AttemptRead, status_code=status.HTTP_201_CREATED)
async def start_attempt(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    test = await db.get(Test, test_id)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    # Students can only take published tests; admins can take any
    if actor.role == "student" and not test.is_published:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Test not available")

    if actor.role == "student":
        if actor.user_id is not None:
            live = await in_progress_full_mock(db, actor.user_id)
            if live is not None and live.test_id == test_id:
                await _ensure_progress_rows_for_attempt(db, live)
                await db.commit()
                await db.refresh(live)
                return live
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Full mocks are assigned automatically",
        )

    # Return existing in-progress FULL MOCK for this user+test (idempotent).
    # Practice attempts live under their own uniqueness scope and never satisfy
    # a "start full mock" request.
    if actor.user_id is not None:
        existing_result = await db.execute(
            select(Attempt).where(
                Attempt.user_id == actor.user_id,
                Attempt.test_id == test_id,
                Attempt.status == AttemptStatus.IN_PROGRESS,
                Attempt.mode == AttemptMode.FULL_MOCK.value,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing is not None:
            await _ensure_progress_rows_for_attempt(db, existing)
            await db.commit()
            await db.refresh(existing)
            return existing

    attempt = Attempt(
        test_id=test_id,
        user_id=actor.user_id,
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
        # Concurrent start — return the winner of the unique index race.
        await db.rollback()
        if actor.user_id is None:
            raise
        raced = await db.execute(
            select(Attempt).where(
                Attempt.user_id == actor.user_id,
                Attempt.test_id == test_id,
                Attempt.status == AttemptStatus.IN_PROGRESS,
                Attempt.mode == AttemptMode.FULL_MOCK.value,
            )
        )
        existing = raced.scalar_one_or_none()
        if existing is None:
            raise
        await _ensure_progress_rows_for_attempt(db, existing)
        await db.commit()
        await db.refresh(existing)
        return existing

    await db.refresh(attempt)
    return attempt


class AnswersSavedResponse(BaseModel):
    saved: int


@router.post("/attempts/{attempt_id}/answers", response_model=AnswersSavedResponse)
async def submit_answers(
    attempt_id: uuid.UUID,
    payload: AnswersBulkSubmit,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    attempt = await _load_attempt_or_404(db, attempt_id, actor)
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attempt already finished")

    answers = list(payload.answers)
    # Single-part writing practice: only accept the targeted task.
    if (
        (attempt.mode or "") == AttemptMode.SINGLE_PART.value
        and (attempt.practice_section_type or "") == SectionType.WRITING.value
        and attempt.practice_part_number is not None
        and answers
    ):
        q_ids = [a.question_id for a in answers]
        q_result = await db.execute(select(Question).where(Question.id.in_(q_ids)))
        allowed = {
            q.id
            for q in q_result.scalars().all()
            if (q.task_number or q.order) == attempt.practice_part_number
        }
        answers = [a for a in answers if a.question_id in allowed]

    now = _now()
    await _enforce_section_writable(
        db,
        attempt,
        [item.question_id for item in answers],
        now,
    )
    saved = await _upsert_answers(db, attempt_id, answers)
    await db.commit()
    return AnswersSavedResponse(saved=saved)


@router.get("/attempts/{attempt_id}/progress", response_model=AttemptProgressRead)
async def get_attempt_progress(
    attempt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    attempt = await _load_attempt_or_404(db, attempt_id, actor)
    await _load_practice_section(db, attempt)
    rows = await _ensure_progress_rows_for_attempt(db, attempt)
    await db.commit()

    now = _now()
    scoped_types = _attempt_progress_types(attempt)
    by_type = {r.section_type: r for r in rows}
    ordered = [by_type[t] for t in scoped_types if t in by_type]
    # Include any stray rows outside scope last (defensive; usually empty).
    for r in rows:
        if r.section_type not in scoped_types:
            ordered.append(r)

    return AttemptProgressRead(
        server_now=now,
        grace_seconds=sp.GRACE_SECONDS,
        sections=[_progress_read(r) for r in ordered],
    )


@router.post(
    "/attempts/{attempt_id}/sections/{section_type}/enter",
    response_model=EnterSectionResponse,
)
async def enter_section(
    attempt_id: uuid.UUID,
    section_type: str,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    if section_type not in _VALID_SECTION_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid section type")

    attempt = await _load_attempt_or_404(db, attempt_id, actor)
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Test not in progress",
        )

    # Lock all progress rows for this attempt to serialize enter races.
    rows = await _ensure_progress_rows_for_attempt(db, attempt, for_update=True)
    settings = await settings_service.ensure_settings(db, attempt.test_id)
    sections = await _load_test_sections(db, attempt.test_id)
    # Practice attempts scope present_types to the single target skill, so the
    # sequential L→R→W→S rule doesn't block a stand-alone Reading Passage 2.
    await _load_practice_section(db, attempt)
    present = _present_types_for_attempt(attempt, sections)
    duration_override = await _practice_duration_override(db, attempt, section_type)
    now = _now()

    try:
        entered, _sealed_prev = sp.apply_enter(
            rows,
            settings,
            section_type,
            now,
            present_types=present,
            duration_override_minutes=duration_override,
        )
    except sp.SectionConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.detail) from exc
    except sp.SectionProgressError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    await db.commit()
    await db.refresh(entered)

    return EnterSectionResponse(
        section_type=entered.section_type,
        state=entered.state if isinstance(entered.state, str) else entered.state.value,
        started_at=entered.started_at,
        ends_at=entered.ends_at,
        sealed_at=entered.sealed_at,
        sealed_reason=entered.sealed_reason,
        server_now=now,
        grace_seconds=sp.GRACE_SECONDS,
    )


@router.post(
    "/attempts/{attempt_id}/sections/{section_type}/seal",
    response_model=SealSectionResponse,
)
async def seal_section(
    attempt_id: uuid.UUID,
    section_type: str,
    payload: SealSectionRequest,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    if section_type not in _VALID_SECTION_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid section type")

    reason = payload.reason or sp.SEAL_REASON_MANUAL
    if reason not in (
        sp.SEAL_REASON_MANUAL,
        sp.SEAL_REASON_TIMEOUT,
        sp.SEAL_REASON_SUBMIT,
        sp.SEAL_REASON_ADVANCE,
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid seal reason")

    attempt = await _load_attempt_or_404(db, attempt_id, actor)
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Test not in progress",
        )

    rows = await _ensure_progress_rows_for_attempt(db, attempt, for_update=True)
    row = sp.find_row(rows, section_type)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section progress not found")

    state = row.state if isinstance(row.state, str) else row.state.value
    if state != SectionState.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Section not active",
        )

    now = _now()

    sections = await _load_test_sections(db, attempt.test_id)
    await _load_practice_section(db, attempt)
    present = _present_types_for_attempt(attempt, sections)

    # Answer flush past grace → same SECTION_EXPIRED path as submit_answers.
    if payload.answers and sp.is_expired(row, now):
        await _raise_section_expired(
            db, rows, row, now, present_types=present
        )

    if payload.answers:
        # Only persist answers that belong to this section (ignore sealed/other).
        answer_qids = [a.question_id for a in payload.answers]
        q_result = await db.execute(
            select(Question.id)
            .join(Section, Section.id == Question.section_id)
            .where(
                Question.id.in_(answer_qids),
                Section.type == section_type,
            )
        )
        allowed_ids = set(q_result.scalars().all())
        scoped = [a for a in payload.answers if a.question_id in allowed_ids]
        if scoped:
            await _upsert_answers(db, attempt_id, scoped)

    if reason == sp.SEAL_REASON_TIMEOUT:
        sp.apply_timeout_seal(row, now)
    else:
        sp.apply_seal(row, reason, now)
    await db.commit()
    await db.refresh(row)

    nxt = sp.next_not_started_type(rows, present)
    return SealSectionResponse(
        sealed=_progress_read(row),
        next_section=nxt,
        all_sealed=sp.all_sealed(rows, present),
        server_now=now,
    )


@router.post("/attempts/{attempt_id}/finish", response_model=AttemptRead)
async def finish_attempt(
    attempt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    attempt = await db.get(Attempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    _assert_attempt_access(attempt, actor)
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attempt already finished")

    if (attempt.mode or AttemptMode.FULL_MOCK.value) in PRACTICE_MODES:
        return await _finish_practice_attempt(db, attempt)

    return await _finish_full_mock_attempt(db, attempt)


async def _finish_full_mock_attempt(
    db: AsyncSession, attempt: Attempt
) -> Attempt:
    """Score and close a full-mock attempt.

    Shared by /finish (student pressed Submit) and /integrity-event (a rule
    violation forced termination) so the seal/score path stays single-sourced.
    """
    attempt_id = attempt.id
    now = datetime.now(timezone.utc)
    attempt.status = AttemptStatus.COMPLETED
    attempt.finished_at = now

    # Seal any remaining open sections.
    rows = await _load_progress_rows(db, attempt_id)
    for row in rows:
        state = row.state if isinstance(row.state, str) else row.state.value
        if state != SectionState.SEALED.value:
            sp.apply_seal(row, sp.SEAL_REASON_SUBMIT, now)

    # Legacy cumulative overtime (started_at + sum(durations) + 10) removed —
    # timing is enforced per-section via SectionProgress.ends_at.
    # attempt.flagged_overtime is no longer written.

    sections_result = await db.execute(
        select(Section)
        .options(selectinload(Section.questions))
        .where(Section.test_id == attempt.test_id)
    )
    sections = sections_result.scalars().all()

    answers_result = await db.execute(
        select(Answer).where(Answer.attempt_id == attempt_id)
    )
    all_answers = answers_result.scalars().all()

    totals: dict[str, list[int]] = {"listening": [0, 0], "reading": [0, 0]}
    attempted: dict[str, bool] = {"listening": False, "reading": False, "writing": False}

    for section in sections:
        section_answers = [a for a in all_answers if any(q.id == a.question_id for q in section.questions)]
        stype = _section_type_str(section.type)

        if stype in ("listening", "reading"):
            if section.questions and section_answers:
                attempted[stype] = True
                correct, _total = score_section(section.questions, section_answers)
                totals[stype][0] += correct
                totals[stype][1] += _total

        elif stype == "writing":
            def _task_key(q) -> str | None:
                tn = q.task_number if q.task_number in (1, 2) else (
                    q.order if q.order in (1, 2) else None
                )
                return f"task_{tn}" if tn is not None else None

            writing_answers = {}
            for a in section_answers:
                for q in section.questions:
                    if q.id == a.question_id:
                        key = _task_key(q)
                        if key:
                            text = a.response.get("answer", "")
                            if isinstance(text, str) and text.strip():
                                attempted["writing"] = True
                            writing_answers[key] = text
            if writing_answers:
                images: dict[str, str] = {}
                prompts: dict[str, str] = {}
                task_descriptions: dict[str, str] = {}
                task_instructions: dict[str, str] = {}
                task_statements: dict[str, str] = {}
                task_questions: dict[str, str] = {}
                essay_types: dict[str, str] = {}
                for q in section.questions:
                    key = _task_key(q)
                    if not key:
                        continue
                    content = q.content if isinstance(q.content, dict) else {}
                    stmt = content.get("task_statement") or ""
                    qn = content.get("task_question") or ""
                    desc = content.get("task_description") or content.get("prompt", "")
                    instr = content.get("task_instruction") or ""
                    prompts[key] = f"{desc}\n\n{instr}".strip() if instr else desc
                    task_descriptions[key] = desc
                    task_instructions[key] = instr
                    task_statements[key] = stmt or desc
                    task_questions[key] = qn
                    img = q.image_url or content.get("image_url")
                    if img:
                        images[key] = img
                    et = getattr(q, "essay_type", None)
                    if et:
                        essay_types[key] = et
                input_data = {
                    "type": "writing",
                    "answers": writing_answers,
                    "prompts": prompts,
                    "task_descriptions": task_descriptions,
                    "task_instructions": task_instructions,
                    "task_statements": task_statements,
                    "task_questions": task_questions,
                    "images": images,
                    "essay_types": essay_types,
                }
                db.add(EvaluationJob(
                    attempt_id=attempt_id,
                    section_type=stype,
                    status=JobStatus.PENDING,
                    input_data=input_data,
                ))

        elif stype == "speaking":
            audio_urls = [
                a.response.get("audio_url", "")
                for a in section_answers
                if a.response.get("audio_url")
            ]
            if audio_urls:
                prompt_texts = []
                for q in section.questions:
                    c = q.content if isinstance(q.content, dict) else {}
                    # New canonical schema: { part, questions: [str] } or { part, cue_card: {...} }
                    if "questions" in c and isinstance(c["questions"], list):
                        prompt_texts.extend(str(p) for p in c["questions"])
                    elif "cue_card" in c and isinstance(c["cue_card"], dict):
                        cc = c["cue_card"]
                        prompt_texts.append(cc.get("topic", "") or str(cc))
                    # Legacy schema: { prompt } or { topic, bullets } or { cue_card: str }
                    elif "prompt" in c:
                        prompt_texts.append(str(c["prompt"]))
                    elif "topic" in c:
                        prompt_texts.append(str(c.get("topic", "")) or str(c))
                    elif "cue_card" in c:
                        prompt_texts.append(str(c["cue_card"]))
                    else:
                        prompt_texts.append(str(q.content))
                input_data = {
                    "type": "speaking",
                    "audio_urls": audio_urls,
                    "prompts": prompt_texts,
                }
                db.add(EvaluationJob(
                    attempt_id=attempt_id,
                    section_type=stype,
                    status=JobStatus.PENDING,
                    input_data=input_data,
                ))

    if attempted["listening"]:
        attempt.listening_band = correct_to_listening_band(totals["listening"][0])
        attempt.listening_raw = totals["listening"][0]
    if attempted["reading"]:
        attempt.reading_band = correct_to_reading_band(totals["reading"][0])
        attempt.reading_raw = totals["reading"][0]

    attempt.overall_band = compute_overall_band(attempt)

    # Flush so we can see pending evaluation jobs created above
    await db.flush()
    jobs_result = await db.execute(
        select(EvaluationJob).where(EvaluationJob.attempt_id == attempt_id)
    )
    pending_jobs = jobs_result.scalars().all()
    if not pending_jobs:
        # L/R-only (or no AI sections answered) — mark auto_scored immediately
        attempt.status = derive_scored_status(attempt)

    await db.commit()

    stmt = (
        select(Attempt)
        .options(selectinload(Attempt.evaluation_jobs))
        .where(Attempt.id == attempt_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


# Event names accepted by /integrity-event. Kept as a whitelist so an unknown
# `type` on the wire cannot poison the log with attacker-controlled strings.
#
# Both names stay accepted even though the client no longer sends them: tabs
# opened before fullscreen proctoring was switched off still report, and a 400
# there would only produce noise in their console.
#   fullscreen_exit   — left fullscreen while the page was live.
#   fullscreen_reload — the exam page loaded outside fullscreen (reload, tab
#                       restore, recovery after a crash).
_INTEGRITY_EVENT_TYPES = frozenset({"fullscreen_exit", "fullscreen_reload"})


# Proctoring events are recorded, never enforced.
#
# Ending an attempt over one of these proved indefensible. A browser drops out
# of fullscreen for reasons the candidate does not control — a permission
# prompt, the window closing, the machine shutting down — and a three-second
# countdown cannot tell any of those from someone walking away. In a single
# morning it closed four live attempts, two belonging to candidates who had
# done nothing wrong.
#
# The events still land in the log for a human to weigh. Ignoring `terminal`
# here rather than only in the client is deliberate: tabs opened before this
# change keep sending it, and they must not be able to close an attempt.
_INTEGRITY_ENFORCED = False


class IntegrityEventIn(BaseModel):
    type: str = Field(..., max_length=64)
    # Sent by clients that still expect the grace window to close the attempt.
    # Accepted for compatibility and ignored; see _INTEGRITY_ENFORCED.
    terminal: bool = False


class IntegrityEventOut(BaseModel):
    recorded: bool
    terminated: bool
    events_count: int


@router.post(
    "/attempts/{attempt_id}/integrity-event",
    response_model=IntegrityEventOut,
)
async def report_integrity_event(
    attempt_id: uuid.UUID,
    payload: IntegrityEventIn,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """Append a proctoring event to the attempt's log.

    Never closes the attempt: see _INTEGRITY_ENFORCED for why.
    """
    if payload.type not in _INTEGRITY_EVENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown integrity event type",
        )

    attempt = await db.get(Attempt, attempt_id)
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found"
        )
    _assert_attempt_access(attempt, actor)
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attempt already finished",
        )

    # JSONB in Postgres is opaque to SQLAlchemy's change tracking when mutated
    # in place, so a fresh list must be assigned for the update to be flushed.
    events = list(attempt.integrity_events or [])
    events.append(
        {
            "type": payload.type,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    attempt.integrity_events = events

    await db.commit()

    # `terminal` is accepted and ignored — see _INTEGRITY_ENFORCED.
    return IntegrityEventOut(
        recorded=True,
        terminated=False,
        events_count=len(events),
    )


@router.get("/attempts/{attempt_id}", response_model=AttemptDetailRead)
async def get_attempt(
    attempt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    stmt = (
        select(Attempt)
        .options(
            selectinload(Attempt.answers).selectinload(Answer.question),
            selectinload(Attempt.evaluation_jobs),
        )
        .where(Attempt.id == attempt_id)
    )
    result = await db.execute(stmt)
    attempt = result.scalar_one_or_none()
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    _assert_attempt_access(attempt, actor)
    return attempt


@router.post("/attempts/{attempt_id}/finalize", response_model=AttemptRead)
async def finalize_attempt(
    attempt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """Explicitly complete an attempt without speaking.

    Transitions from auto_scored → completed_without_speaking,
    keeping speaking_band None and recomputing overall from L/R/W only.
    """
    from app.models.speaking_session import SpeakingSession

    attempt = await db.get(Attempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    _assert_attempt_access(attempt, actor)

    if attempt.status not in (AttemptStatus.AUTO_SCORED, AttemptStatus.SPEAKING_IN_PROGRESS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot finalize attempt with status '{attempt.status}'",
        )

    attempt.speaking_band = None
    attempt.overall_band = compute_overall_band(attempt)
    attempt.status = AttemptStatus.COMPLETED_WITHOUT_SPEAKING

    # Abandon any lingering speaking sessions for this attempt
    sessions_result = await db.execute(
        select(SpeakingSession).where(
            SpeakingSession.attempt_id == attempt_id,
            SpeakingSession.status == "in_progress",
        )
    )
    for session in sessions_result.scalars().all():
        session.status = "abandoned"

    await db.commit()
    await db.refresh(attempt)
    return attempt


class SpeakingScoreSubmit(BaseModel):
    speaking_band: float = Field(..., ge=0, le=9)
    score_json: dict | None = None
    session_id: uuid.UUID | None = None


@router.post("/attempts/{attempt_id}/speaking-score", response_model=AttemptRead)
async def submit_speaking_score(
    attempt_id: uuid.UUID,
    payload: SpeakingScoreSubmit,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """Write the Speaking band score back to a test attempt and recompute overall band."""
    from app.models.speaking_session import SpeakingSession

    attempt = await db.get(Attempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    _assert_attempt_access(attempt, actor)

    # Admins may supply an arbitrary band (teacher override).
    # Students must prove ownership of a scored session; band is derived server-side.
    band_to_use = payload.speaking_band
    score_json = payload.score_json

    if actor.role != "admin":
        if payload.session_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session_id is required",
            )
        session = await db.get(SpeakingSession, payload.session_id)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.admin_email != actor.sub:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")
        server_band = session.overall_band
        if server_band is None and isinstance(session.score_json, dict):
            server_band = session.score_json.get("overall_band")
        if server_band is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session has not been scored yet",
            )
        band_to_use = float(server_band)
        if session.score_json:
            score_json = session.score_json

    attempt.speaking_band = band_to_use
    attempt.overall_band = compute_overall_band(attempt)

    # Seal speaking section when score is written back.
    rows = await _load_progress_rows(db, attempt_id)
    speaking_row = sp.find_row(rows, SectionType.SPEAKING.value)
    if speaking_row is not None:
        state = speaking_row.state if isinstance(speaking_row.state, str) else speaking_row.state.value
        if state != SectionState.SEALED.value:
            sp.apply_seal(speaking_row, sp.SEAL_REASON_MANUAL, _now())

    # Promote status once writing/async jobs are resolved
    if attempt.status in (
        AttemptStatus.AUTO_SCORED,
        AttemptStatus.SPEAKING_IN_PROGRESS,
        AttemptStatus.FULLY_SCORED,
        AttemptStatus.COMPLETED,
    ):
        jobs_result = await db.execute(
            select(EvaluationJob).where(EvaluationJob.attempt_id == attempt_id)
        )
        jobs = jobs_result.scalars().all()
        writing_pending = any(
            j.section_type == "writing"
            and j.status in (JobStatus.PENDING, JobStatus.PROCESSING)
            for j in jobs
        )
        if not writing_pending:
            attempt.status = derive_scored_status(attempt)

    if payload.session_id is not None:
        session = await db.get(SpeakingSession, payload.session_id)
        if session is not None:
            if actor.role == "admin" or session.admin_email == actor.sub:
                session.attempt_id = attempt_id
                session.test_id = attempt.test_id
                if session.overall_band is None:
                    session.overall_band = band_to_use
                if score_json and session.score_json is None:
                    session.score_json = score_json
                session.status = "completed"
                session.finished_at = datetime.now(timezone.utc)

    if score_json:
        db.add(EvaluationJob(
            attempt_id=attempt_id,
            section_type="speaking",
            status=JobStatus.DONE,
            input_data={},
            result=score_json,
            band_score=band_to_use,
            processed_at=datetime.now(timezone.utc),
        ))

    await db.commit()
    await db.refresh(attempt)
    return attempt
