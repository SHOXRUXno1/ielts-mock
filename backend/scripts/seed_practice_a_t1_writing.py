"""Seed Practice Set A Test 1 Writing, Task 1 and Task 2.

Task 1: bar chart of world illiteracy rates by region and gender, 2000.
Task 2: agree/disagree on dropping non-academic school subjects.

One deliberate departure from the paper. Its Task 1 rubric says "literacy
rates" while the chart it prints is titled "illiteracy rates". Left as printed,
a candidate who reads the chart correctly would be marked down for contradicting
the prompt, so the rubric here follows the chart.

Idempotent: the writing section is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t1_writing.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.models.question import Question, QuestionType  # noqa: E402
from app.models.question_group import QuestionGroup  # noqa: E402
from app.models.section import SectionType  # noqa: E402
from app.services.writing_presets import get_default_instruction  # noqa: E402
from seed_practice_a_common import (  # noqa: E402
    CHART_IMAGE_URL,
    clear_section,
    get_section,
    get_test,
)

TEST_NUMBER = 1

TASK1_DESCRIPTION = (
    "The chart below shows estimated world illiteracy rates by region and by "
    "gender for the year 2000."
)

TASK2_STATEMENT = (
    "With the pressures on today's young people to succeed academically, some "
    "people believe that non-academic subjects at school (eg: physical "
    "education and cookery) should be removed from the syllabus so that "
    "children can concentrate wholly on academic subjects."
)
TASK2_QUESTION = "To what extent do you agree or disagree?"
TASK2_ESSAY_TYPE = "opinion"


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    section = await get_section(db, test.id, SectionType.WRITING, 20)
    print(f"Test: {test.title} ({test.id})")
    print(f"Writing section {section.id}  removed "
          f"{await clear_section(db, section.id)} old row(s)")

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
    print(f"  Task 1  chart {CHART_IMAGE_URL.format(test=TEST_NUMBER)}  min 150 words")
    print(f"  Task 2  {TASK2_ESSAY_TYPE}  min 250 words")
    print("\nDone. Writing seeded.")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
