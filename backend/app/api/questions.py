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
from app.schemas.question import QuestionCreate, QuestionRead, QuestionUpdate

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
    return result.scalars().all()


@router.post("/", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
async def create_question(
    section_id: uuid.UUID,
    payload: QuestionCreate,
    db: AsyncSession = Depends(get_db),
):
    section = await _get_section(section_id, db)

    data = payload.model_dump(exclude={"question_group_id"})

    # Writing-specific validation
    if payload.question_type == QuestionType.ESSAY:
        data = await _validate_and_normalise_writing(data, section, db)

    # If no group_id is given, auto-create/reuse a wrapper QuestionGroup for this type
    group_id = payload.question_group_id
    if group_id is None:
        existing = await db.execute(
            select(QuestionGroup)
            .where(
                QuestionGroup.section_id == section_id,
                QuestionGroup.question_type == payload.question_type,
            )
            .order_by(QuestionGroup.order)
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

    question = Question(section_id=section_id, question_group_id=group_id, **data)
    db.add(question)
    await db.commit()
    await db.refresh(question)
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

    for field, value in data.items():
        setattr(question, field, value)

    await db.commit()
    await db.refresh(question)
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

    # SQL-level DELETE so PostgreSQL ON DELETE CASCADE removes related answers
    # (ORM db.delete() tries to nullify answers.question_id first → NOT NULL error)
    await db.execute(delete(Question).where(Question.id == question_id))
    await db.commit()
