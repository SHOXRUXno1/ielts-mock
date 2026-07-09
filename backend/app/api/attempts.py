import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import Actor, get_current_actor
from app.core.database import get_db
from app.models.answer import Answer
from app.models.attempt import Attempt, AttemptStatus
from app.models.evaluation_job import EvaluationJob, JobStatus
from app.models.question import Question
from app.models.section import Section, SectionType
from app.models.test import Test
from app.schemas.attempt import AnswersBulkSubmit, AttemptDetailRead, AttemptRead
from app.services.band_calc import compute_overall_band
from app.services.scoring import (
    correct_to_listening_band,
    correct_to_reading_band,
    score_section,
)

router = APIRouter(tags=["Attempts"])


def _section_type_str(section_type: SectionType | str) -> str:
    return section_type.value if isinstance(section_type, SectionType) else section_type


def _assert_attempt_access(attempt: Attempt, actor: Actor) -> None:
    """Students can only access their own attempts."""
    if actor.role == "student" and attempt.user_id != actor.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


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

    # Auto-abandon any previous in_progress attempt for the same user+test
    if actor.user_id is not None:
        stale_result = await db.execute(
            select(Attempt).where(
                Attempt.user_id == actor.user_id,
                Attempt.test_id == test_id,
                Attempt.status == AttemptStatus.IN_PROGRESS,
            )
        )
        for stale in stale_result.scalars().all():
            stale.status = AttemptStatus.ABANDONED
        await db.flush()

    attempt = Attempt(
        test_id=test_id,
        user_id=actor.user_id,  # None for .env admin, UUID for DB users
        status=AttemptStatus.IN_PROGRESS,
        started_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    await db.commit()
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
    attempt = await db.get(Attempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    _assert_attempt_access(attempt, actor)
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attempt already finished")

    existing_q = await db.execute(
        select(Answer.question_id).where(Answer.attempt_id == attempt_id)
    )
    existing_ids = set(existing_q.scalars().all())

    for item in payload.answers:
        if item.question_id in existing_ids:
            result = await db.execute(
                select(Answer).where(
                    Answer.attempt_id == attempt_id,
                    Answer.question_id == item.question_id,
                )
            )
            ans = result.scalar_one()
            ans.response = item.response
        else:
            db.add(Answer(
                attempt_id=attempt_id,
                question_id=item.question_id,
                response=item.response,
            ))

    await db.commit()
    return AnswersSavedResponse(saved=len(payload.answers))


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

    now = datetime.now(timezone.utc)
    attempt.status = AttemptStatus.COMPLETED
    attempt.finished_at = now

    if attempt.started_at:
        elapsed_minutes = (now - attempt.started_at).total_seconds() / 60
        sections_for_time = await db.execute(
            select(Section).where(Section.test_id == attempt.test_id)
        )
        all_sections_for_time = sections_for_time.scalars().all()
        allowed_minutes = (
            sum(s.duration_minutes for s in all_sections_for_time) + 10
        )
        if elapsed_minutes > allowed_minutes:
            attempt.flagged_overtime = True

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

    for section in sections:
        section_answers = [a for a in all_answers if any(q.id == a.question_id for q in section.questions)]
        stype = _section_type_str(section.type)

        if stype in ("listening", "reading"):
            if section.questions and section_answers:
                correct, _total = score_section(section.questions, section_answers)
                totals[stype][0] += correct
                totals[stype][1] += _total

        elif stype == "writing":
            writing_answers = {}
            for a in section_answers:
                for q in section.questions:
                    if q.id == a.question_id:
                        writing_answers[f"task_{q.order}"] = a.response.get("answer", "")
            if writing_answers:
                images: dict[str, str] = {}
                for q in section.questions:
                    # Prefer the new DB column; fall back to legacy content JSON field
                    img = q.image_url or (
                        q.content.get("image_url") if isinstance(q.content, dict) else None
                    )
                    if img:
                        images[f"task_{q.order}"] = img
                input_data = {
                    "type": "writing",
                    "answers": writing_answers,
                    "prompts": {
                        f"task_{q.order}": q.content.get("prompt", "")
                        for q in section.questions
                    },
                    "images": images,
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

    if totals["listening"][0] > 0 or totals["listening"][1] > 0:
        attempt.listening_band = correct_to_listening_band(totals["listening"][0])
        attempt.listening_raw = totals["listening"][0]
    if totals["reading"][0] > 0 or totals["reading"][1] > 0:
        attempt.reading_band = correct_to_reading_band(totals["reading"][0])
        attempt.reading_raw = totals["reading"][0]

    attempt.overall_band = compute_overall_band(attempt)

    await db.commit()

    stmt = (
        select(Attempt)
        .options(selectinload(Attempt.evaluation_jobs))
        .where(Attempt.id == attempt_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/attempts/{attempt_id}", response_model=AttemptDetailRead)
async def get_attempt(
    attempt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    stmt = (
        select(Attempt)
        .options(selectinload(Attempt.answers), selectinload(Attempt.evaluation_jobs))
        .where(Attempt.id == attempt_id)
    )
    result = await db.execute(stmt)
    attempt = result.scalar_one_or_none()
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    _assert_attempt_access(attempt, actor)
    return attempt


class SpeakingScoreSubmit(BaseModel):
    speaking_band: float = Field(..., ge=0, le=9)
    score_json: dict | None = None


@router.post("/attempts/{attempt_id}/speaking-score", response_model=AttemptRead)
async def submit_speaking_score(
    attempt_id: uuid.UUID,
    payload: SpeakingScoreSubmit,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    """Write the Speaking band score back to a test attempt and recompute overall band."""
    attempt = await db.get(Attempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    _assert_attempt_access(attempt, actor)

    attempt.speaking_band = payload.speaking_band
    attempt.overall_band = compute_overall_band(attempt)

    if payload.score_json:
        db.add(EvaluationJob(
            attempt_id=attempt_id,
            section_type="speaking",
            status=JobStatus.DONE,
            input_data={},
            result=payload.score_json,
            band_score=payload.speaking_band,
            processed_at=datetime.now(timezone.utc),
        ))

    await db.commit()
    await db.refresh(attempt)
    return attempt
