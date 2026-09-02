"""Seed Practice Set D Test 3 Speaking, Parts 1-3.

Wording is taken from the printed paper (p.110). Examiner admin
questions are omitted. Teaching tip strips are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t3_speaking.py
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

TEST_NUMBER = 3

PART1_CONTENT = {
    "part": 1,
    "topic": "School",
    "questions": [
        "What subject did you find most interesting when you were at school?",
        "Apart from classes, what else did you enjoy at school?",
        "Do you think that you will stay friends with people from your school?",
        "What study or training would you like to do in the future?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a holiday you would like to go on",
        "bullets": [
            "what place you would like to go to",
            "how you would like to get there",
            "what you would like to do while you were there",
        ],
        "follow_up": "and explain why you would like to go on this holiday",
    },
    "rounding_off": [],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Tourism",
        "Holidays",
    ],
    "questions": [
        "Which places in your country do you think visitors would enjoy visiting most?",
        "What are the benefits of going away on holiday?",
        "What kinds of benefits might a significant increase in tourist "
        "numbers bring to a location?",
        "What developments affecting international travel might there be "
        "in the future?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 \u2014 School"),
    (
        31,
        PART2_CONTENT,
        "Part 2 \u2014 Describe a holiday you would like to go on",
    ),
    (32, PART3_CONTENT, "Part 3 \u2014 Tourism"),
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
