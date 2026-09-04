"""Seed Practice Set E Test 4 Speaking, Parts 1-3.

Source: Peter May Oxford IELTS Practice Tests, Test 4 (pp.117-118).
Exam questions only — no "Improve your skills" exercises, no
strategy boxes.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_e_t4_speaking.py
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
from seed_practice_e_common import clear_section, get_section, get_test  # noqa: E402

TEST_NUMBER = 4

PART1_CONTENT = {
    "part": 1,
    "topic": "Language learning / Visitors / Communicating",
    "questions": [
        "What is your full name?",
        "What do people usually call you?",
        "Where are you from?",
        "What are your earliest memories of learning English?",
        "What do you find difficult about English?",
        "What do you enjoy about learning it?",
        "Which other languages have you studied?",
        "What are the main tourist attractions there?",
        "What else would you recommend to foreign visitors?",
        "Does/Would mass tourism benefit your country? Why?/Why not?",
        "How do you keep in touch with your family and friends?",
        "Tell me about an important message you have received.",
        "How have mobile phones changed the way people communicate?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a present which you very much enjoyed receiving",
        "bullets": [
            "what it was",
            "who gave it to you",
            "what the occasion was",
        ],
        "follow_up": "and explain why you were so pleased to receive it",
    },
    "rounding_off": [
        "Which do you enjoy more: giving or receiving presents?",
        "Do you like presents to be a surprise, or do you prefer "
        "to choose what you are given?",
    ],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Giving gifts",
        "Charities",
        "Helping other countries",
    ],
    "questions": [
        "On what occasions do people in your country give each other "
        "presents?",
        "Do you feel the commercialization of gift-giving, e.g. Christmas "
        "in certain countries, has gone too far?",
        "What is the role of charities nowadays?",
        "Which charity would you like to be able to give a lot of "
        "money to?",
        "Should rich countries give much more financial assistance "
        "to poorer ones?",
        "How can we encourage more young people to do voluntary "
        "work abroad?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (
        30,
        PART1_CONTENT,
        "Part 1 \u2014 Language learning, visitors, communicating",
    ),
    (
        31,
        PART2_CONTENT,
        "Part 2 \u2014 Describe a present you enjoyed receiving",
    ),
    (
        32,
        PART3_CONTENT,
        "Part 3 \u2014 Giving gifts, charities, helping other countries",
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
