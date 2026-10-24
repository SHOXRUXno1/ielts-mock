"""Seed Practice Set D Test 1 Writing.

Source: Collins Practice Tests for IELTS 3 (2021), Test 1 (pp.25-26).

Task 1: table — projected growth of global freight by 2050 and
        projected carbon dioxide emissions (Air, Road, Rail, Sea for
        2010 and 2050 with growth percentages).
Task 2: discuss both views — e-books replacing paper books vs both
        existing side by side.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t1_writing.py
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
from seed_practice_d_common import (  # noqa: E402
    clear_section,
    get_section,
    get_test,
)

TEST_NUMBER = 1
TASK1_IMAGE_URL = "/media/images/practice_d_t1_writing_task1_v2.svg?v=2"

TASK1_DESCRIPTION = (
    "The table below shows the projected growth of global freight by "
    "2050 and how this will affect carbon dioxide (CO₂) emissions.\n\n"
    "Summarise the information by selecting and reporting the main "
    "features, and make comparisons where relevant."
)

TASK2_STATEMENT = (
    "Some people think that e-books will eventually replace traditional "
    "paper-based books. Others, however, believe that both versions will "
    "continue to exist side by side."
)
TASK2_QUESTION = "Discuss both these views and give your own opinion."
TASK2_ESSAY_TYPE = "discussion"


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
    task1_description = TASK1_DESCRIPTION
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
            image_url=TASK1_IMAGE_URL,
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
    print(f"  Task 1  chart {TASK1_IMAGE_URL}  min 150 words")
    print(f"  Task 2  {TASK2_ESSAY_TYPE}  min 250 words")
    print("\nDone. Writing seeded.")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
