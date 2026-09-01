"""Seed Practice Set C Test 7 Writing.

Task 1: pie chart comparison — Internet activities by age group.
Task 2: opinion — legal age for marriage.

Wording is taken from the printed paper (p.151). The teaching tip strips
around those tasks are not part of the exam and are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t7_writing.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.models.question import Question, QuestionType  # noqa: E402
from app.models.question_group import QuestionGroup  # noqa: E402
from app.models.section import SectionType  # noqa: E402
from app.services.writing_presets import get_default_instruction  # noqa: E402
from seed_practice_c_common import (  # noqa: E402
    CHART_IMAGE_URL,
    clear_section,
    get_section,
    get_test,
)

TEST_NUMBER = 7

TASK1_DESCRIPTION = (
    "The pie charts below show the percentage of time younger and older "
    "people spend on various Internet activities in their free time "
    "(excluding email).\n\n"
    "Summarise the information by selecting and reporting the main features, "
    "and make comparisons where relevant."
)

TASK2_STATEMENT = (
    "Some people feel that the legal age at which people can marry should "
    "be at least 21."
)
TASK2_QUESTION = (
    "To what extent do you agree or disagree?"
)
TASK2_ESSAY_TYPE = "opinion"


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    section = await get_section(db, test.id, SectionType.WRITING, 20)
    print(f"Test: {test.title} ({test.id})")
    print(
        f"Writing section {section.id}  removed "
        f"{await clear_section(db, section.id)} old row(s)"
    )

    group = QuestionGroup(
        id=uuid.uuid4(),
        section_id=section.id,
        order=1,
        question_type=QuestionType.ESSAY.value,
        instruction="",
        options_shared=None,
    )
    db.add(group)
    await db.flush()

    task1_instruction = get_default_instruction(1)
    task1_description = (
        f"{TASK1_DESCRIPTION}\n\n"
        "You should spend about 20 minutes on this task."
    )
    db.add(
        Question(
            id=uuid.uuid4(),
            section_id=section.id,
            question_group_id=group.id,
            order=1,
            question_type=QuestionType.ESSAY,
            content={
                "task_description": task1_description,
                "task_instruction": task1_instruction,
                "prompt": f"{task1_description}\n\n{task1_instruction}",
            },
            answer_key=None,
            task_number=1,
            min_words=150,
            image_url=CHART_IMAGE_URL.format(test=TEST_NUMBER),
            essay_type=None,
        )
    )

    task2_instruction = get_default_instruction(2, TASK2_ESSAY_TYPE)
    task2_description = f"{TASK2_STATEMENT}\n\n{TASK2_QUESTION}"
    db.add(
        Question(
            id=uuid.uuid4(),
            section_id=section.id,
            question_group_id=group.id,
            order=2,
            question_type=QuestionType.ESSAY,
            content={
                "task_statement": TASK2_STATEMENT,
                "task_question": TASK2_QUESTION,
                "use_custom_question": True,
                "task_description": task2_description,
                "task_instruction": task2_instruction,
                "prompt": f"{task2_description}\n\n{task2_instruction}",
            },
            answer_key=None,
            task_number=2,
            min_words=250,
            image_url=None,
            essay_type=TASK2_ESSAY_TYPE,
        )
    )

    await db.commit()
    print("\nDone. Writing seeded (Task 1 + Task 2).")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
