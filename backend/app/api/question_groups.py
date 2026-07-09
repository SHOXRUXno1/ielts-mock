"""CRUD for QuestionGroup + question-in-group creation."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.question import Question
from app.models.question_group import QuestionGroup
from app.models.section import Section
from app.schemas.question import QuestionCreateInGroup, QuestionRead
from app.schemas.question_group import QuestionGroupCreate, QuestionGroupRead, QuestionGroupUpdate

router = APIRouter(
    tags=["Question Groups"],
    dependencies=[Depends(get_current_admin)],
)


async def _get_section(section_id: uuid.UUID, db: AsyncSession) -> Section:
    section = await db.get(Section, section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    return section


async def _get_group(group_id: uuid.UUID, db: AsyncSession) -> QuestionGroup:
    result = await db.execute(
        select(QuestionGroup)
        .where(QuestionGroup.id == group_id)
        .options(selectinload(QuestionGroup.questions))
    )
    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question group not found")
    return group


def _synthesize_groups_from_questions(
    questions: list[Question],
) -> list[QuestionGroupRead]:
    """Build synthetic groups from orphan questions (contiguous same type)."""
    from app.services.question_grouping import group_questions_by_contiguous_type

    groups: list[QuestionGroupRead] = []
    for order, run in enumerate(
        group_questions_by_contiguous_type(questions, lambda q: q.question_type), start=1
    ):
        groups.append(
            QuestionGroupRead(
                id=uuid.uuid4(),
                section_id=run[0].section_id,
                order=order,
                question_type=run[0].question_type,
                instruction="",
                options_shared=None,
                questions=[QuestionRead.model_validate(q) for q in run],
                created_at=run[0].created_at,
                updated_at=run[0].updated_at,
            )
        )
    return groups


@router.get(
    "/admin/sections/{section_id}/question-groups",
    response_model=list[QuestionGroupRead],
)
async def list_question_groups(
    section_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    await _get_section(section_id, db)

    # Fetch actual groups with nested questions
    result = await db.execute(
        select(QuestionGroup)
        .where(QuestionGroup.section_id == section_id)
        .options(selectinload(QuestionGroup.questions))
        .order_by(QuestionGroup.order)
    )
    groups = list(result.scalars().all())

    # Fetch orphan questions (no group) and synthesize groups for them
    orphan_result = await db.execute(
        select(Question)
        .where(Question.section_id == section_id, Question.question_group_id.is_(None))
        .order_by(Question.order)
    )
    orphans = list(orphan_result.scalars().all())
    synthetic = _synthesize_groups_from_questions(orphans)

    return [QuestionGroupRead.model_validate(g) for g in groups] + synthetic


@router.post(
    "/admin/sections/{section_id}/question-groups",
    response_model=QuestionGroupRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_question_group(
    section_id: uuid.UUID,
    payload: QuestionGroupCreate,
    db: AsyncSession = Depends(get_db),
):
    await _get_section(section_id, db)

    # Auto-compute order = max + 1 if not provided
    if payload.order is None:
        max_result = await db.execute(
            select(func.coalesce(func.max(QuestionGroup.order), 0)).where(
                QuestionGroup.section_id == section_id
            )
        )
        payload_order = (max_result.scalar() or 0) + 1
    else:
        payload_order = payload.order

    group = QuestionGroup(
        section_id=section_id,
        order=payload_order,
        question_type=payload.question_type,
        instruction=payload.instruction,
        options_shared=payload.options_shared,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)

    result = await db.execute(
        select(QuestionGroup)
        .where(QuestionGroup.id == group.id)
        .options(selectinload(QuestionGroup.questions))
    )
    return result.scalar_one()


@router.patch(
    "/admin/question-groups/{group_id}",
    response_model=QuestionGroupRead,
)
async def update_question_group(
    group_id: uuid.UUID,
    payload: QuestionGroupUpdate,
    db: AsyncSession = Depends(get_db),
):
    group = await _get_group(group_id, db)
    data = payload.model_dump(exclude_unset=True)
    new_question_type = data.get("question_type")

    for field, value in data.items():
        setattr(group, field, value)

    # Bulk-update all questions in the group when the group type changes
    if new_question_type and new_question_type != group.question_type:
        await db.execute(
            update(Question)
            .where(Question.question_group_id == group_id)
            .values(question_type=new_question_type)
        )

    await db.commit()
    await db.refresh(group)

    result = await db.execute(
        select(QuestionGroup)
        .where(QuestionGroup.id == group_id)
        .options(selectinload(QuestionGroup.questions))
    )
    return result.scalar_one()


@router.delete(
    "/admin/question-groups/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_question_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    group = await _get_group(group_id, db)
    # SQL-level DELETE so CASCADE removes questions + related answers
    await db.execute(delete(QuestionGroup).where(QuestionGroup.id == group.id))
    await db.commit()


@router.post(
    "/admin/question-groups/{group_id}/questions",
    response_model=QuestionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_question_in_group(
    group_id: uuid.UUID,
    payload: QuestionCreateInGroup,
    db: AsyncSession = Depends(get_db),
):
    group = await _get_group(group_id, db)

    # Inherit question_type from group when not provided
    if payload.question_type is None:
        effective_type = group.question_type
    elif payload.question_type != group.question_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"question_type '{payload.question_type}' does not match "
                f"group question_type '{group.question_type}'. "
                "Omit question_type to inherit from the group."
            ),
        )
    else:
        effective_type = payload.question_type

    # Auto-compute order within the group
    max_result = await db.execute(
        select(func.coalesce(func.max(Question.order), 0)).where(
            Question.question_group_id == group_id
        )
    )
    auto_order = (max_result.scalar() or 0) + 1
    order = payload.order if payload.order != 1 or auto_order == 1 else auto_order

    question = Question(
        section_id=group.section_id,
        question_group_id=group_id,
        order=order,
        question_type=effective_type,
        content=payload.content,
        answer_key=payload.answer_key,
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question
