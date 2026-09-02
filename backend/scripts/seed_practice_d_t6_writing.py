"""Seed Practice Set D Test 6 Writing.

Task 1: Pie charts — teachers' survey on why students learn foreign
        languages + recent change in reasons.
Task 2: Work vs hobbies/leisure — Discuss both attitudes and give
        your own opinion (discussion essay).

Wording from the printed paper (pp.168-169). Tip strips omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t6_writing.py
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
    CHART_IMAGE_URL,
    clear_section,
    get_section,
    get_test,
)

TEST_NUMBER = 6

TASK1_DESCRIPTION = (
    "The pie charts below show responses by teachers of foreign "
    "languages in Britain to a survey concerning why their students "
    "are learning a foreign language. The first chart shows the main "
    "reason for learning a foreign language. The second chart shows "
    "how many teachers felt that there has been a recent change in "
    "the reason.\n\n"
    "Write a report for a university lecturer describing the "
    "information below.\n\n"
    "Summarise the information by selecting and reporting the main "
    "features, and make comparisons where relevant."
)

TASK2_STATEMENT = (
    "Some people regard work as the most important thing in life "
    "and have little interest in anything else. Other people are "
    "more enthusiastic about their hobbies and leisure interests "
    "than their jobs."
)
TASK2_QUESTION = (
    "Discuss both these attitudes and give your own opinion."
)
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
