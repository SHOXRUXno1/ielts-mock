import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import Actor, get_current_actor
from app.core.database import get_db
from app.models.answer import Answer
from app.models.attempt import Attempt
from app.models.evaluation_job import EvaluationJob
from app.models.question import Question
from app.models.section import Section
from app.models.test import Test
from app.schemas.attempt import (
    AnswerRead,
    AttemptDetailRead,
    AttemptRead,
    EvaluationJobRead,
    QuestionSnapshot,
    SectionSnapshot,
)
from app.services.band_calc import compute_overall_band

router = APIRouter(prefix="/results", tags=["Results"])


class AttemptListItem(AttemptRead):
    test_title: str


class OverrideBand(BaseModel):
    band: float


@router.get("/", response_model=list[AttemptListItem])
async def list_results(
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(get_current_actor),
):
    stmt = (
        select(Attempt, Test.title)
        .join(Test, Attempt.test_id == Test.id)
        .order_by(Attempt.created_at.desc())
    )
    # Students see only their own results
    if actor.role == "student":
        stmt = stmt.where(Attempt.user_id == actor.user_id)

    result = await db.execute(stmt)
    items = []
    for attempt, title in result.all():
        base = AttemptRead.model_validate(attempt)
        d = AttemptListItem(**base.model_dump(), test_title=title)
        items.append(d)
    return items


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

    # Students can only see their own
    if actor.role == "student" and attempt.user_id != actor.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Build enriched AnswerRead list with question + section snapshots
    answers_out: list[AnswerRead] = []
    for a in attempt.answers:
        q: Question | None = a.question
        sec: Section | None = q.section if q is not None else None
        answers_out.append(
            AnswerRead(
                id=a.id,
                question_id=a.question_id,
                response=a.response,
                is_correct=a.is_correct,
                score=a.score,
                question=QuestionSnapshot.model_validate(q) if q is not None else None,
                section=SectionSnapshot.model_validate(sec) if sec is not None else None,
            )
        )

    return AttemptDetailRead(
        **AttemptRead.model_validate(attempt).model_dump(),
        answers=answers_out,
        evaluation_jobs=[EvaluationJobRead.model_validate(j) for j in attempt.evaluation_jobs],
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
        await db.commit()

    await db.refresh(job)
    return job
