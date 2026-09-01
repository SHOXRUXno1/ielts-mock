"""Seed Practice Set D Test 2 Speaking, Parts 1-3.

Wording is taken from the printed paper (pp.88-91). Examiner admin
questions (name / nationality) are omitted — the platform already
identifies the student. Teaching tip strips are not part of the exam
and are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t2_speaking.py
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

TEST_NUMBER = 2

PART1_CONTENT = {
    "part": 1,
    "topic": "Journeys and transport",
    "questions": [
        "What journeys do you make every day?",
        "What do you do during journeys?",
        "Do you sometimes have problems with transport?",
        "What is your favourite form of transport?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a conversation you had which was important to you",
        "bullets": [
            "when the conversation took place",
            "who you had the conversation with",
            "what the conversation was about",
        ],
        "follow_up": (
            "and explain why the conversation was important to you"
        ),
    },
    "rounding_off": [
        "Do you have many important conversations?",
        "Who do you usually have important conversations with?",
    ],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Communication",
        "Channels of communication",
    ],
    "questions": [
        "What differences are there when using channels of communication "
        "(face-to-face, telephone, writing)?",
        "To what extent do you think films and TV influence how people "
        "communicate with each other?",
        "Do you think that there are differences in the way men and "
        "women communicate?",
        "Do you agree that education has a strong and positive effect "
        "on people\u2019s ability to communicate effectively?",
        "What impact do you think the growth of technology might have "
        "on communication in the future?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 \u2014 Journeys and transport"),
    (
        31,
        PART2_CONTENT,
        "Part 2 \u2014 Describe a conversation you had which was "
        "important to you",
    ),
    (
        32,
        PART3_CONTENT,
        "Part 3 \u2014 Communication",
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
