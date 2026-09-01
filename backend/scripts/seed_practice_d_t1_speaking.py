"""Seed Practice Set D Test 1 Speaking, Parts 1-3.

Wording is taken from the printed paper (pp.48-50). Examiner admin
questions (name / nationality) are omitted — the platform already
identifies the student. Teaching tip strips are not part of the exam
and are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t1_speaking.py
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

TEST_NUMBER = 1

PART1_CONTENT = {
    "part": 1,
    "topic": "Friends",
    "questions": [
        "How much time do you spend with friends?",
        "What kinds of things do you like to do with your friends?",
        "What kinds of work or studies do your friends do?",
        "What does being a good friend mean to you?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a party you went to which you enjoyed",
        "bullets": [
            "where the party was",
            "why the party happened",
            "who was at the party",
        ],
        "follow_up": "and explain why you enjoyed the party",
    },
    "rounding_off": [
        "Do other people you know like parties?",
        "Do you often go to parties?",
    ],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Social events",
        "Social life and leisure",
    ],
    "questions": [
        "What kinds of social events are most popular in your country?",
        "What are the differences between the social events that older "
        "and younger people enjoy?",
        "Do you think it is a good idea for colleagues at work to spend "
        "time socially together?",
        "What changes have there been recently in social life in your "
        "country?",
        "Would you agree that technology can have negative effects on "
        "the way people spend their leisure time?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 \u2014 Friends"),
    (
        31,
        PART2_CONTENT,
        "Part 2 \u2014 Describe a party you went to which you enjoyed",
    ),
    (
        32,
        PART3_CONTENT,
        "Part 3 \u2014 Social events and leisure",
    ),
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
