import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section, SectionType
from app.models.test import Test
from app.schemas.question import QuestionCreate, QuestionRead, QuestionUpdate, validate_multi_select_answers
from app.services.compound import is_compound_type, validate_compound_gap_content
from app.services.question_numbering import (
    annotate_questions_list,
    question_numbers_for_test,
)
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)
_LEGACY_CONTENT_KEYS = ("task_type", "min_words", "image_url")

router = APIRouter(
    prefix="/admin/sections/{section_id}/questions",
    tags=["Questions"],
    dependencies=[Depends(get_current_admin)],
)

_WRITING_MIN_WORDS = {1: 150, 2: 250}


async def _get_section(section_id: uuid.UUID, db: AsyncSession) -> Section:
    section = await db.get(Section, section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    return section


async def _annotate_questions_in_section(
    section_id: uuid.UUID,
    questions: list[Question],
    db: AsyncSession,
) -> None:
    """Load the parent test graph and set computed_number on *questions*."""
    section = await db.get(Section, section_id)
    if section is None:
        return
    stmt = (
        select(Test)
        .options(
            selectinload(Test.sections)
            .selectinload(Section.question_groups)
            .selectinload(QuestionGroup.questions),
            selectinload(Test.sections).selectinload(Section.questions),
        )
        .where(Test.id == section.test_id)
    )
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()
    if test is None:
        return
    annotate_questions_list(questions, question_numbers_for_test(test))


async def next_question_order(section_id: uuid.UUID, db: AsyncSession) -> int:
    """Return max(order)+1 within the section (1 if empty)."""
    max_result = await db.execute(
        select(func.coalesce(func.max(Question.order), 0)).where(
            Question.section_id == section_id
        )
    )
    return (max_result.scalar() or 0) + 1


async def next_question_order_in_group(
    group_id: uuid.UUID, db: AsyncSession
) -> int:
    """Return max(order)+1 within the question group (1 if empty).

    Order is a local position inside the group (1, 2, 3…), not a
    section-wide absolute index. IELTS display numbers are computed
    separately from cumulative scoring slots across groups.
    """
    max_result = await db.execute(
        select(func.coalesce(func.max(Question.order), 0)).where(
            Question.question_group_id == group_id
        )
    )
    return (max_result.scalar() or 0) + 1


async def assert_order_available(
    section_id: uuid.UUID,
    order: int,
    db: AsyncSession,
    *,
    exclude_question_id: uuid.UUID | None = None,
) -> None:
    """Raise 400 if another question in the section already uses this order."""
    stmt = select(Question.id).where(
        Question.section_id == section_id,
        Question.order == order,
    )
    if exclude_question_id is not None:
        stmt = stmt.where(Question.id != exclude_question_id)
    existing = await db.execute(stmt.limit(1))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already exists",
        )


async def assert_order_available_in_group(
    group_id: uuid.UUID,
    order: int,
    db: AsyncSession,
    *,
    exclude_question_id: uuid.UUID | None = None,
) -> None:
    """Raise 400 if another question in the same group already uses this order."""
    stmt = select(Question.id).where(
        Question.question_group_id == group_id,
        Question.order == order,
    )
    if exclude_question_id is not None:
        stmt = stmt.where(Question.id != exclude_question_id)
    existing = await db.execute(stmt.limit(1))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already exists",
        )


async def _validate_and_normalise_writing(
    payload_data: dict,
    section: Section,
    db: AsyncSession,
) -> dict:
    """For essay questions, enforce writing-task rules and normalise metadata.

    Rules:
    - task_number must be 1 or 2.
    - min_words is always 150 (task 1) or 250 (task 2) — not editable by client.
    - image_url is only allowed on Task 1 of an Academic test; rejected on Task 2.
    """
    task_number = payload_data.get("task_number")
    image_url = payload_data.get("image_url")

    if task_number not in (1, 2):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Writing tasks must have task_number 1 or 2.",
        )

    # Force correct min_words regardless of what client sent
    payload_data["min_words"] = _WRITING_MIN_WORDS[task_number]

    # Task 1 must never carry essay_type
    if task_number == 1:
        payload_data["essay_type"] = None

    if task_number == 2 and image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task 2 (Essay) must not have a chart/diagram image.",
        )

    if task_number == 1 and image_url:
        # Verify parent test is Academic before allowing a chart image
        result = await db.execute(
            select(Test.type).join(Section, Section.test_id == Test.id).where(Section.id == section.id)
        )
        test_type = result.scalar_one_or_none()
        if test_type and test_type.lower() != "academic":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Chart/diagram images are only allowed for Academic Writing Task 1. "
                    f"This test type is '{test_type}'."
                ),
            )

    return payload_data


@router.get("/", response_model=list[QuestionRead])
async def list_questions(section_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await _get_section(section_id, db)
    result = await db.execute(
        select(Question).where(Question.section_id == section_id).order_by(Question.order)
    )
    questions = list(result.scalars().all())
    await _annotate_questions_in_section(section_id, questions, db)
    return questions


@router.post("/", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
async def create_question(
    section_id: uuid.UUID,
    payload: QuestionCreate,
    db: AsyncSession = Depends(get_db),
):
    section = await _get_section(section_id, db)

    data = payload.model_dump(exclude={"question_group_id"})

    # Warn if client still sends legacy content keys (stripped by schema, but log for monitoring)
    raw_content = payload.content or {}
    leaked = [k for k in _LEGACY_CONTENT_KEYS if k in raw_content]
    if leaked:
        logger.warning(
            "Legacy content field(s) %s received on create for section %s, ignoring",
            leaked,
            section_id,
        )

    # Writing-specific validation
    if payload.question_type == QuestionType.ESSAY:
        if section.type == SectionType.WRITING or str(section.type) == "writing":
            count_result = await db.execute(
                select(func.count())
                .select_from(Question)
                .where(
                    Question.section_id == section_id,
                    Question.question_type == QuestionType.ESSAY,
                )
            )
            essay_count = count_result.scalar() or 0
            if essay_count >= 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Writing section already has 2 tasks. Cannot add a third essay question.",
                )
        data = await _validate_and_normalise_writing(data, section, db)

    # Questions always belong to a group. If no group_id is given, auto-create
    # or reuse a wrapper QuestionGroup for this type (never leave question_group_id NULL).
    group_id = payload.question_group_id
    if group_id is None:
        if is_compound_type(payload.question_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Compound completion questions must be created inside a "
                    "question group that already has a structure in options_shared. "
                    "Create a question group first."
                ),
            )
        # Prefer the last group of this type in the section (continue editing).
        existing = await db.execute(
            select(QuestionGroup)
            .where(
                QuestionGroup.section_id == section_id,
                QuestionGroup.question_type == payload.question_type,
            )
            .order_by(QuestionGroup.order.desc())
            .limit(1)
        )
        group = existing.scalar_one_or_none()
        if group is None:
            max_result = await db.execute(
                select(func.coalesce(func.max(QuestionGroup.order), 0)).where(
                    QuestionGroup.section_id == section_id
                )
            )
            next_order = (max_result.scalar() or 0) + 1
            group = QuestionGroup(
                section_id=section_id,
                order=next_order,
                question_type=payload.question_type,
                instruction="",
                options_shared=None,
            )
            db.add(group)
            await db.flush()
        group_id = group.id
    else:
        group = await db.get(QuestionGroup, group_id)
        if group is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question group not found",
            )
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

    await assert_order_available_in_group(group_id, data["order"], db)

    question = Question(section_id=section_id, question_group_id=group_id, **data)
    db.add(question)
    await db.commit()
    await db.refresh(question)
    await _annotate_questions_in_section(section_id, [question], db)
    return question


@router.patch("/{question_id}", response_model=QuestionRead)
async def update_question(
    section_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
):
    question = await db.get(Question, question_id)
    if question is None or question.section_id != section_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    data = payload.model_dump(exclude_unset=True)

    if "content" in data and isinstance(data["content"], dict):
        leaked = [k for k in _LEGACY_CONTENT_KEYS if k in (payload.content or {})]
        if leaked:
            logger.warning(
                "Legacy content field(s) %s received for question %s, ignoring",
                leaked,
                question_id,
            )

    # Group type guard: if this question belongs to a group, its type must match
    if question.question_group_id is not None and "question_type" in data:
        group = await db.get(QuestionGroup, question.question_group_id)
        if group is not None and data["question_type"] != group.question_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"question_type '{data['question_type']}' does not match "
                    f"group question_type '{group.question_type}'."
                ),
            )

    # Compound gap_id must stay in sync with group structure
    if question.question_group_id is not None and "content" in data:
        group = await db.get(QuestionGroup, question.question_group_id)
        if group is not None and is_compound_type(group.question_type):
            try:
                validate_compound_gap_content(
                    group.question_type,
                    group.options_shared,
                    data["content"],
                )
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc

    # Writing-specific validation when updating an essay question
    effective_type = data.get("question_type", question.question_type)
    if effective_type == QuestionType.ESSAY or str(effective_type) == "essay":
        # Merge task_number from existing if not provided in this update
        if "task_number" not in data:
            data["task_number"] = question.task_number
        if "image_url" not in data:
            data["image_url"] = question.image_url

        section = await _get_section(section_id, db)
        data = await _validate_and_normalise_writing(data, section, db)

    effective_type_str = getattr(effective_type, "value", effective_type)
    if effective_type_str == "multi_select" and (
        "content" in data or "answer_key" in data or "question_type" in data
    ):
        merged_content = data["content"] if "content" in data else (question.content or {})
        merged_key = data["answer_key"] if "answer_key" in data else question.answer_key
        try:
            validate_multi_select_answers(
                str(effective_type_str), merged_content, merged_key
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

    if "order" in data and data["order"] != question.order:
        if question.question_group_id is not None:
            await assert_order_available_in_group(
                question.question_group_id,
                data["order"],
                db,
                exclude_question_id=question_id,
            )
        else:
            await assert_order_available(
                section_id,
                data["order"],
                db,
                exclude_question_id=question_id,
            )

    for field, value in data.items():
        setattr(question, field, value)

    await db.commit()
    await db.refresh(question)
    await _annotate_questions_in_section(section_id, [question], db)
    return question


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    section_id: uuid.UUID,
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    question = await db.get(Question, question_id)
    if question is None or question.section_id != section_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    # Writing Task 1/2 are required — refuse deletion
    is_essay = (
        question.question_type == QuestionType.ESSAY
        or str(question.question_type) == "essay"
    )
    if is_essay and question.task_number in (1, 2):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Writing Task {question.task_number} is required and cannot be deleted.",
        )

    # SQL-level DELETE so PostgreSQL ON DELETE CASCADE removes related answers
    # (ORM db.delete() tries to nullify answers.question_id first → NOT NULL error)
    await db.execute(delete(Question).where(Question.id == question_id))
    await db.commit()
