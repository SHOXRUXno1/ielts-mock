"""CRUD for QuestionGroup + question-in-group creation."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.question import Question
from app.models.question_group import QuestionGroup
from app.models.section import Section
from app.api.questions import (
    assert_order_available_in_group,
    next_question_order_in_group,
    _annotate_questions_in_section,
)
from app.schemas.question import (
    QuestionCreateInGroup,
    QuestionRead,
    validate_multi_select_answers,
)
from app.schemas.question_group import QuestionGroupCreate, QuestionGroupRead, QuestionGroupUpdate
from app.services.compound import (
    extract_gap_ids,
    is_compound_type,
    validate_compound_gap_content,
    validate_compound_structure,
)
from app.services.section_types import is_type_allowed

# Auto-convert legacy short names to canonical types on create/update
_LEGACY_TYPE_MAP: dict[str, str] = {
    "table": "table_completion",
    "notes": "note_completion",
    "form": "form_completion",
    "flow": "flow_chart_completion",
}


def _normalise_question_type(raw: str) -> str:
    return _LEGACY_TYPE_MAP.get(raw, raw)


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
                subtitle=None,
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
    section = await _get_section(section_id, db)

    payload.question_type = _normalise_question_type(payload.question_type)

    section_type_value = section.type.value if hasattr(section.type, "value") else str(section.type)
    if not is_type_allowed(section_type_value, payload.question_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This question type is not allowed in {section_type_value} sections",
        )

    if is_compound_type(payload.question_type):
        try:
            validate_compound_structure(payload.question_type, payload.options_shared)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

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
        subtitle=payload.subtitle,
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
    previous_type = group.question_type
    new_question_type = data.get("question_type")

    if new_question_type is not None:
        new_question_type = _normalise_question_type(new_question_type)
        data["question_type"] = new_question_type

    if new_question_type is not None and new_question_type != previous_type:
        section = await db.get(Section, group.section_id)
        if section:
            section_type_value = section.type.value if hasattr(section.type, "value") else str(section.type)
            if not is_type_allowed(section_type_value, new_question_type):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"This question type is not allowed in {section_type_value} sections",
                )

    effective_type = new_question_type if new_question_type is not None else group.question_type
    effective_options = (
        data["options_shared"] if "options_shared" in data else group.options_shared
    )
    if is_compound_type(effective_type):
        try:
            validate_compound_structure(effective_type, effective_options)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

    for field, value in data.items():
        setattr(group, field, value)

    # Bulk-update all questions in the group when the group type changes
    if new_question_type and new_question_type != previous_type:
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

    try:
        validate_multi_select_answers(
            effective_type, payload.content, payload.answer_key
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    if is_compound_type(group.question_type):
        try:
            validate_compound_gap_content(
                group.question_type,
                group.options_shared,
                payload.content,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        # Upsert by gap_id: if a question for this gap already exists in the
        # group, update it in place rather than creating a duplicate.
        gap_id = payload.content.get("gap_id") if isinstance(payload.content, dict) else None
        if gap_id:
            existing_for_gap = next(
                (
                    q for q in group.questions
                    if isinstance(q.content, dict) and q.content.get("gap_id") == gap_id
                ),
                None,
            )
            if existing_for_gap is not None:
                existing_for_gap.content = payload.content
                existing_for_gap.answer_key = payload.answer_key
                existing_for_gap.question_type = effective_type
                await db.commit()
                await db.refresh(existing_for_gap)
                await _annotate_questions_in_section(
                    group.section_id, [existing_for_gap], db
                )
                return existing_for_gap

    # Prefer client-provided order; otherwise:
    # - compound gaps: position of gap_id in structure (deterministic 1..N)
    # - other types: max(group)+1
    # Order is local to the group. IELTS display numbers are computed separately.
    if payload.order is None:
        gap_id = (
            payload.content.get("gap_id")
            if is_compound_type(group.question_type) and isinstance(payload.content, dict)
            else None
        )
        if gap_id:
            positions = {
                gid: i + 1
                for i, gid in enumerate(extract_gap_ids(group.options_shared))
            }
            preferred = positions.get(gap_id)
            if preferred is not None:
                # Use gap position when free; otherwise fall back to max+1
                clash = await db.execute(
                    select(Question.id).where(
                        Question.question_group_id == group_id,
                        Question.order == preferred,
                    ).limit(1)
                )
                if clash.scalar_one_or_none() is None:
                    order = preferred
                else:
                    order = await next_question_order_in_group(group_id, db)
            else:
                order = await next_question_order_in_group(group_id, db)
        else:
            order = await next_question_order_in_group(group_id, db)
    else:
        order = payload.order
        await assert_order_available_in_group(group_id, order, db)

    question = Question(
        section_id=group.section_id,
        question_group_id=group_id,
        order=order,
        question_type=effective_type,
        content=payload.content,
        answer_key=payload.answer_key,
    )
    db.add(question)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A question with order {order} already exists in this group.",
        )
    await db.refresh(question)
    await _annotate_questions_in_section(group.section_id, [question], db)
    return question
