"""Seed Practice Set D Test 4 Speaking, Parts 1-3.

Wording is taken from the printed paper (p.130). Examiner admin
questions are omitted. Teaching tip strips are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t4_speaking.py
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
from seed_practice_d_common import clear_section, get_section, get_test  # noqa: E402

TEST_NUMBER = 4

PART1_CONTENT = {
    "part": 1,
    "topic": "Food",
    "questions": [
        "What sorts of food do you enjoy eating most?",
        "Do you spend much time shopping for food?",
        "Which do you prefer, eating at home or eating in restaurants?",
        "Do you think people should be careful about what they eat?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a town you have enjoyed visiting",
        "bullets": [
            "why you went to the town",
            "who you saw there",
            "what you did there",
        ],
        "follow_up": "and explain why you enjoyed visiting the town",
    },
    "rounding_off": [],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Visiting towns and cities",
        "City vs countryside",
        "Congestion",
    ],
    "questions": [
        "What are the kinds of things people like to do when visiting towns and cities?",
        "Why do many people prefer to live in cities rather than in the countryside?",
        "Can you identify some of the main problems of living in large cities?",
        "What measures could be taken to reduce problems of congestion in cities?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 \u2014 Food"),
    (
        31,
        PART2_CONTENT,
        "Part 2 \u2014 Describe a town you have enjoyed visiting",
    ),
    (32, PART3_CONTENT, "Part 3 \u2014 Cities"),
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
        print(f"  {label}  removed {removed} old row(s)")

    await db.commit()
    print("\nDone. Speaking seeded (Parts 1\u20133).")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
