"""Seed Cambridge IELTS 15 Test 1 Writing Task 2 (owning a home).

Keeps existing Task 1. Idempotent for Task 2 only.

Usage (prod container):
    python /tmp/seed_ielts15_t1_writing_t2.py
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section
from app.models.test import Test
from app.services.seed_compound import next_group_order
from app.services.writing_presets import get_default_instruction

TEST_ID = uuid.UUID("6528e947-1883-4318-bca0-8fb9face3590")
WRITING_ID = uuid.UUID("81904976-4f9d-4726-9aaa-bbb14e9fbad6")

STATEMENT = (
    "In some countries, owning a home rather than renting one is very "
    "important for people."
)
TASK_QUESTION = (
    "Why might this be the case?\n\n"
    "Do you think this is a positive or negative situation?"
)
ESSAY_TYPE = "double_question"


async def seed(db: AsyncSession) -> None:
    test = await db.get(Test, TEST_ID)
    if test is None:
        raise SystemExit(f"Test {TEST_ID} not found")
    section = await db.get(Section, WRITING_ID)
    if section is None or section.test_id != TEST_ID:
        raise SystemExit(f"Writing section {WRITING_ID} not found")

    print(f"Test: {test.title}")
    print(f"Writing section: {section.id}")

    existing = (
        await db.execute(
            select(Question).where(
                Question.section_id == WRITING_ID,
                Question.question_type == QuestionType.ESSAY,
                Question.task_number == 2,
            )
        )
    ).scalars().all()
    group_ids = {q.question_group_id for q in existing}
    for q in existing:
        await db.delete(q)
    await db.flush()

    for gid in group_ids:
        remaining = (
            await db.execute(
                select(Question).where(Question.question_group_id == gid)
            )
        ).scalars().all()
        if not remaining:
            g = await db.get(QuestionGroup, gid)
            if g is not None:
                await db.delete(g)
    await db.flush()

    group = (
        await db.execute(
            select(QuestionGroup)
            .where(
                QuestionGroup.section_id == WRITING_ID,
                QuestionGroup.question_type == QuestionType.ESSAY,
            )
            .order_by(QuestionGroup.order.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if group is None:
        group = QuestionGroup(
            section_id=WRITING_ID,
            order=await next_group_order(db, WRITING_ID),
            question_type=QuestionType.ESSAY,
            instruction="",
            options_shared=None,
        )
        db.add(group)
        await db.flush()

    instruction = get_default_instruction(2, ESSAY_TYPE)
    full_desc = f"{STATEMENT}\n\n{TASK_QUESTION}"
    content = {
        "task_statement": STATEMENT,
        "task_question": TASK_QUESTION,
        "use_custom_question": True,
        "task_description": full_desc,
        "task_instruction": instruction,
        "prompt": f"{full_desc}\n\n{instruction}".strip(),
    }

    q = Question(
        section_id=WRITING_ID,
        question_group_id=group.id,
        order=2,
        question_type=QuestionType.ESSAY,
        content=content,
        answer_key=None,
        task_number=2,
        min_words=250,
        image_url=None,
        essay_type=ESSAY_TYPE,
    )
    db.add(q)
    await db.commit()
    await db.refresh(q)

    print(f"  Task 2 id={q.id}")
    print(f"  essay_type={q.essay_type}")
    print(f"  min_words={q.min_words}")
    print(f"  statement={STATEMENT}")
    print(f"  question={TASK_QUESTION!r}")
    print("Done. Writing Task 2 seeded. Task 1 unchanged.")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
