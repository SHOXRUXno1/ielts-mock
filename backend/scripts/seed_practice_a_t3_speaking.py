"""Seed Practice Set A Test 3 Speaking, Parts 1-3.

Part 1: work or study, then Schooldays, then Rivers.
Part 2: describe your favourite restaurant.
Part 3: Fast Food, then Food Problems.

The paper offers two topics in Parts 1 and 3; both are kept, which is how a real
examiner works through the part.

Idempotent: each part section is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t3_speaking.py
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
from seed_practice_a_common import clear_section, get_section, get_test  # noqa: E402

TEST_NUMBER = 3

PART1_CONTENT = {
    "part": 1,
    "topic": "Schooldays / Rivers",
    "questions": [
        "Tell me about the job or studies that you are doing.",
        "Why did you choose this field?",
        "Do you think you will ever change this job or study? [Why/Why not?]",
        "What were the good parts and the bad parts about your schooldays?",
        "What was your favourite subject at school? [Why?]",
        "How did your school teach sports?",
        "How would you improve the school that you went to?",
        "Describe a river in your country.",
        "What kinds of things are rivers used for in your country?",
        "Are there any pollution problems with rivers in your country? [What?]",
        "What kind of problems do people face if they live near a big river?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "your favourite restaurant",
        "bullets": [
            "where the restaurant is and how you found it",
            "what type of food it serves",
            "how often you go there",
        ],
        "follow_up": "and explain exactly why you like this restaurant so much",
    },
}

PART3_CONTENT = {
    "part": 3,
    "topics": ["Fast Food", "Food Problems"],
    "questions": [
        "Is fast food popular in your country? [Why?]",
        "Why has fast food become so popular over the last 30 years?",
        "Could you compare fast food with traditional meals?",
        "How can we stop young people eating so much fast food?",
        "What are some of the problems that some countries have with food "
        "production?",
        "Could you suggest any ways to solve these problems?",
        "What other problems can you predict happening in terms of food in the "
        "next 50 years?",
        "Could you compare methods of food production and distribution today with "
        "that of 50 years ago?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 — Work or study, schooldays, rivers"),
    (31, PART2_CONTENT, "Part 2 — A favourite restaurant"),
    (32, PART3_CONTENT, "Part 3 — Fast food and food problems"),
]


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")

    for order, content, label in PARTS:
        section = await get_section(db, test.id, SectionType.SPEAKING, order)
        removed = await clear_section(db, section.id)
        section.title = label

        group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=1,
            question_type=QuestionType.SPEAKING_PART.value,
            instruction="",
            options_shared=None,
        )
        db.add(group)
        await db.flush()

        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=section.id,
                question_group_id=group.id,
                order=1,
                question_type=QuestionType.SPEAKING_PART,
                content=content,
                answer_key=None,
            )
        )
        prompts = (
            len(content["questions"])
            if "questions" in content
            else len(content["cue_card"]["bullets"])
        )
        print(f"  {label}  removed {removed} old row(s)  {prompts} prompts")

    await db.commit()
    print("\nDone. Speaking Parts 1-3 seeded.")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
