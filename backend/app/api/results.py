import asyncio
import io
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import Actor, get_current_actor
from app.core.database import get_db
from app.models.answer import Answer
from app.models.attempt import Attempt, AttemptMode, AttemptStatus
from app.models.evaluation_job import EvaluationJob, JobStatus
from app.models.question import Question
from app.models.question_group import QuestionGroup
from app.models.section import Section, SectionType
from app.models.speaking_session import SpeakingSession
from app.models.test import Test
from app.models.user import User
from app.schemas.attempt import (
    AnswerRead,
    AttemptDetailRead,
    AttemptRead,
    EvaluationJobRead,
    QuestionSnapshot,
    SectionSnapshot,
    SpeakingSessionSummary,
)
from app.services.band_calc import compute_overall_band, derive_scored_status
from app.services.result_report import (
    build_report_context,
    content_disposition,
    render_report_pdf,
    report_filenames,
)
from app.services.question_numbering import annotate_questions_list, question_numbers_for_test
from app.services.scoring import (
    correct_to_listening_band,
    correct_to_reading_band,
    score_section,
)
from app.utils.labels import format_test_label

router = APIRouter(prefix="/results", tags=["Results"])

SCORED_STATUSES = {
    AttemptStatus.AUTO_SCORED,
    AttemptStatus.FULLY_SCORED,
    AttemptStatus.COMPLETED_WITHOUT_SPEAKING,
}


class AttemptListItem(AttemptRead):
    test_title: str
    student_name: str | None = None
    student_id: str | None = None


class PaginatedAttemptList(BaseModel):
    items: list[AttemptListItem]
    total: int
    limit: int
    offset: int = Field(ge=0)


class OverrideBand(BaseModel):
    band: float


class StudentInfo(BaseModel):
    """Admin-facing student profile fields for results analytics."""

    id: str
    full_name: str
    login: str
    phone: str | None = None
    group_name: str | None = None
    is_active: bool = True
    created_at: datetime


class StudentResultStats(BaseModel):
    attempts_count: int
    best_band: float | None
    average_band: float | None
    last_attempt_at: datetime | None


class BandProgressionPoint(BaseModel):
    attempt_id: str
    band: float
    date: datetime
    test_name: str


class SectionAverages(BaseModel):
    listening: float | None
    reading: float | None
    writing: float | None
    speaking: float | None


class StudentResultsResponse(BaseModel):
    student: StudentInfo
    stats: StudentResultStats
    band_progression: list[BandProgressionPoint]
    section_averages: SectionAverages
    attempts: list[AttemptListItem]


def _section_type_str(section_type: SectionType | str) -> str:
    return section_type.value if isinstance(section_type, SectionType) else section_type


def _task_key(q: Question) -> str | None:
    tn = q.task_number if q.task_number in (1, 2) else (
        q.order if q.order in (1, 2) else None
    )
    return f"task_{tn}" if tn is not None else None


def _require_admin(actor: Actor) -> None:
    if actor.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


async def _attempt_list_item(db: AsyncSession, attempt: Attempt) -> AttemptListItem:
    test = await db.get(Test, attempt.test_id)
    user = await db.get(User, attempt.user_id) if attempt.user_id else None
    base = AttemptRead.model_validate(attempt)
    return AttemptListItem(
        **base.model_dump(),
        test_title=format_test_label(test.title, test.test_number) if test else "",
        student_name=user.full_name if user else None,
        student_id=str(user.id) if user else None,
    )


@router.get("/", response_model=PaginatedAttemptList)
async def list_results(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    filters = []
    if actor.role == "student":
        # Students only see full-mock attempts here; practice attempts live
        # under /student/practice-results.
        filters.extend(
            [
                Attempt.user_id == actor.user_id,
                Attempt.mode == AttemptMode.FULL_MOCK.value,
            ]
        )

    total = (
        await db.execute(select(func.count(Attempt.id)).where(*filters))
    ).scalar_one()

    stmt = (
        select(
            Attempt,
            Test.title,
            Test.test_number,
            User.full_name,
            User.id.label("uid"),
        )
        .join(Test, Attempt.test_id == Test.id)
        .outerjoin(User, Attempt.user_id == User.id)
        .where(*filters)
        .order_by(Attempt.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)
    items = []
    for attempt, title, test_number, user_name, uid in result.all():
        base = AttemptRead.model_validate(attempt)
        d = AttemptListItem(
            **base.model_dump(),
            test_title=format_test_label(title, test_number),
            student_name=user_name,
            student_id=str(uid) if uid else None,
        )
        items.append(d)
    return PaginatedAttemptList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/students/{student_id}", response_model=StudentResultsResponse)
async def student_results(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    _require_admin(actor)

    user = await db.get(User, student_id)
    if user is None or user.role != "student":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    stmt = (
        select(Attempt, Test.title, Test.test_number)
        .join(Test, Attempt.test_id == Test.id)
        .where(Attempt.user_id == student_id)
        .order_by(Attempt.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()

    attempts: list[AttemptListItem] = []
    for attempt, title, test_number in rows:
        base = AttemptRead.model_validate(attempt)
        attempts.append(
            AttemptListItem(
                **base.model_dump(),
                test_title=format_test_label(title, test_number),
                student_name=user.full_name,
                student_id=str(user.id),
            )
        )

    scored_status_values = {s.value for s in SCORED_STATUSES}
    scored = [
        a for a in attempts
        if a.status in scored_status_values
        and a.overall_band is not None
        and a.overall_band > 0
    ]
    bands = [a.overall_band for a in scored if a.overall_band is not None]
    last_at = attempts[0].created_at if attempts else None

    progression_src = scored[:10]
    band_progression = [
        BandProgressionPoint(
            attempt_id=str(a.id),
            band=a.overall_band,  # type: ignore[arg-type]
            date=a.finished_at or a.created_at,
            test_name=a.test_title,
        )
        for a in reversed(progression_src)
        if a.overall_band is not None
    ]

    def _avg(vals: list[float]) -> float | None:
        return round(sum(vals) / len(vals), 1) if vals else None

    section_averages = SectionAverages(
        listening=_avg([a.listening_band for a in scored if a.listening_band is not None]),
        reading=_avg([a.reading_band for a in scored if a.reading_band is not None]),
        writing=_avg([a.writing_band for a in scored if a.writing_band is not None]),
        speaking=_avg([a.speaking_band for a in scored if a.speaking_band is not None]),
    )

    return StudentResultsResponse(
        student=StudentInfo(
            id=str(user.id),
            full_name=user.full_name,
            login=user.login,
            phone=user.phone,
            group_name=user.group_name,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
        stats=StudentResultStats(
            attempts_count=len(attempts),
            best_band=max(bands) if bands else None,
            average_band=round(sum(bands) / len(bands), 1) if bands else None,
            last_attempt_at=last_at,
        ),
        band_progression=band_progression,
        section_averages=section_averages,
        attempts=attempts,
    )


@router.delete("/{attempt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attempt(
    attempt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    _require_admin(actor)
    attempt = await db.get(Attempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    await db.delete(attempt)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{attempt_id}/re-score", response_model=AttemptListItem)
async def rescore_attempt(
    attempt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    _require_admin(actor)

    attempt = await db.get(Attempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    if attempt.status == AttemptStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot re-score an in-progress attempt",
        )

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
    has_new_jobs = False

    for section in sections:
        section_answers = [
            a for a in all_answers if any(q.id == a.question_id for q in section.questions)
        ]
        stype = _section_type_str(section.type)

        if stype in ("listening", "reading"):
            if section.questions and section_answers:
                attempted[stype] = True
                correct, _total = score_section(section.questions, section_answers)
                totals[stype][0] += correct
                totals[stype][1] += _total

        elif stype == "writing":
            writing_answers: dict[str, str] = {}
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
                    stmt_text = content.get("task_statement") or ""
                    qn = content.get("task_question") or ""
                    desc = content.get("task_description") or content.get("prompt", "")
                    instr = content.get("task_instruction") or ""
                    prompts[key] = f"{desc}\n\n{instr}".strip() if instr else desc
                    task_descriptions[key] = desc
                    task_instructions[key] = instr
                    task_statements[key] = stmt_text or desc
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
                has_new_jobs = True

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
                    if "questions" in c and isinstance(c["questions"], list):
                        prompt_texts.extend(str(p) for p in c["questions"])
                    elif "cue_card" in c and isinstance(c["cue_card"], dict):
                        cc = c["cue_card"]
                        prompt_texts.append(cc.get("topic", "") or str(cc))
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
                has_new_jobs = True

    if attempted["listening"]:
        attempt.listening_band = correct_to_listening_band(totals["listening"][0])
        attempt.listening_raw = totals["listening"][0]
    if attempted["reading"]:
        attempt.reading_band = correct_to_reading_band(totals["reading"][0])
        attempt.reading_raw = totals["reading"][0]

    attempt.overall_band = compute_overall_band(attempt)

    if has_new_jobs:
        attempt.status = AttemptStatus.COMPLETED
    else:
        attempt.status = derive_scored_status(attempt)

    await db.commit()
    await db.refresh(attempt)
    return await _attempt_list_item(db, attempt)


@router.get("/{attempt_id}", response_model=AttemptDetailRead)
async def get_result_detail(
    attempt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    stmt = (
        select(Attempt)
        .options(
            selectinload(Attempt.answers)
            .selectinload(Answer.question)
            .selectinload(Question.section),
            selectinload(Attempt.evaluation_jobs),
        )
        .where(Attempt.id == attempt_id)
    )
    result = await db.execute(stmt)
    attempt = result.scalar_one_or_none()
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")

    if actor.role == "student" and attempt.user_id != actor.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    test_stmt = (
        select(Test)
        .options(
            selectinload(Test.sections)
            .selectinload(Section.question_groups)
            .selectinload(QuestionGroup.questions),
            selectinload(Test.sections).selectinload(Section.questions),
        )
        .where(Test.id == attempt.test_id)
    )
    test_result = await db.execute(test_stmt)
    test = test_result.scalar_one_or_none()
    ranges = question_numbers_for_test(test) if test is not None else {}

    # Collect ALL listening/reading questions from the test graph so we can
    # annotate them and synthesize unanswered entries later.
    all_lr_questions: list[Question] = []
    question_to_section: dict[uuid.UUID, Section] = {}
    if test is not None:
        for sec in test.sections:
            stype = sec.type.value if hasattr(sec.type, "value") else str(sec.type)
            if stype not in ("listening", "reading"):
                continue
            for q in (sec.questions or []):
                if q.question_type in ("essay", "speaking_part"):
                    continue
                all_lr_questions.append(q)
                question_to_section[q.id] = sec

    # Annotate both answered questions AND all L/R questions for IELTS numbers.
    qs_to_annotate = [a.question for a in attempt.answers if a.question is not None]
    qs_to_annotate.extend(
        q for q in all_lr_questions if q.id not in {aq.id for aq in qs_to_annotate}
    )
    annotate_questions_list(qs_to_annotate, ranges)

    hide_answer_key = (
        actor.role == "student"
        and attempt.status in (AttemptStatus.IN_PROGRESS, AttemptStatus.SPEAKING_IN_PROGRESS)
    )

    answers_out: list[AnswerRead] = []
    answered_qids: set[uuid.UUID] = set()
    for a in attempt.answers:
        answered_qids.add(a.question_id)
        q: Question | None = a.question
        sec: Section | None = q.section if q is not None else None
        q_snap = QuestionSnapshot.model_validate(q) if q is not None else None
        if q_snap is not None and hide_answer_key:
            q_snap.answer_key = None
        answers_out.append(
            AnswerRead(
                id=a.id,
                question_id=a.question_id,
                response=a.response,
                is_correct=a.is_correct,
                score=a.score,
                question=q_snap,
                section=SectionSnapshot.model_validate(sec) if sec is not None else None,
            )
        )

    # Synthesize unanswered entries for skipped listening/reading questions.
    for q in all_lr_questions:
        if q.id in answered_qids:
            continue
        sec = question_to_section.get(q.id)
        q_snap = QuestionSnapshot.model_validate(q)
        if hide_answer_key:
            q_snap.answer_key = None
        answers_out.append(
            AnswerRead(
                id=q.id,
                question_id=q.id,
                response={},
                is_correct=False,
                score=0.0,
                question=q_snap,
                section=SectionSnapshot.model_validate(sec) if sec is not None else None,
            )
        )

    speaking_session_out: SpeakingSessionSummary | None = None
    sess_result = await db.execute(
        select(SpeakingSession)
        .where(SpeakingSession.attempt_id == attempt_id)
        .order_by(SpeakingSession.created_at.desc())
        .limit(1)
    )
    sess = sess_result.scalar_one_or_none()
    if sess is not None:
        speaking_session_out = SpeakingSessionSummary.model_validate(sess)

    return AttemptDetailRead(
        **AttemptRead.model_validate(attempt).model_dump(),
        answers=answers_out,
        evaluation_jobs=[EvaluationJobRead.model_validate(j) for j in attempt.evaluation_jobs],
        speaking_session=speaking_session_out,
        test_title=(
            format_test_label(test.title, test.test_number)
            if test is not None
            else None
        ),
    )


async def _attempt_student_name(
    db: AsyncSession,
    attempt_id: uuid.UUID,
    actor: Actor,
) -> str:
    if actor.role == "student" and actor.db_user is not None:
        name = getattr(actor.db_user, "full_name", None)
        if name:
            return str(name)
        if actor.login:
            return actor.login
    stmt = (
        select(User.full_name)
        .join(Attempt, Attempt.user_id == User.id)
        .where(Attempt.id == attempt_id)
    )
    name = (await db.execute(stmt)).scalar_one_or_none()
    return name or "Student"


@router.get("/{attempt_id}/pdf")
async def download_result_pdf(
    attempt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    detail = await get_result_detail(attempt_id, db, actor)
    student_name = await _attempt_student_name(db, attempt_id, actor)
    context = build_report_context(detail, student_name)
    pdf = await asyncio.to_thread(render_report_pdf, context)
    ascii_name, utf8_name = report_filenames(detail)
    return StreamingResponse(
        io.BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": content_disposition(ascii_name, utf8_name)},
    )


@router.patch("/jobs/{job_id}/override", response_model=EvaluationJobRead)
async def override_band(
    job_id: uuid.UUID,
    payload: OverrideBand,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    if actor.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    job = await db.get(EvaluationJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation job not found")

    job.teacher_override_band = payload.band
    await db.commit()

    attempt = await db.get(Attempt, job.attempt_id)
    if attempt is not None:
        band = job.teacher_override_band
        if job.section_type == "writing":
            attempt.writing_band = band
        elif job.section_type == "speaking":
            attempt.speaking_band = band

        attempt.overall_band = compute_overall_band(attempt)
        if attempt.status in (
            AttemptStatus.AUTO_SCORED,
            AttemptStatus.FULLY_SCORED,
            AttemptStatus.COMPLETED,
        ):
            attempt.status = derive_scored_status(attempt)
        await db.commit()

    await db.refresh(job)
    return job
