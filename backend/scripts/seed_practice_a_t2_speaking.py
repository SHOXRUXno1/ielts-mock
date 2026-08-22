"""Seed Practice Set A Test 2 Speaking, Parts 1-3.

Part 1: where the candidate lives, then Studying English, then Transport.
Part 2: describe what would be the perfect holiday.
Part 3: Tourism, then Holidays.

Idempotent: each part section is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t2_speaking.py
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

TEST_NUMBER = 2

PART1_CONTENT = {
    "part": 1,
    "topic": "Studying English / Transport",
    "questions": [
        "Tell me about the part of the country where you live.",
        "What are the main ways of earning money in this area?",
        "What are some of the advantages and disadvantages of living in this area?",
        "Where have you studied English?",
        "What do you find most difficult about studying English?",
        "What's the best way for you to study English?",
        "How can speaking English well help you in your life?",
        "What is the best way to get around the place where you live?",
        "How would you improve transport in your town or area?",
        "How does transport cause pollution?",
        "Do people prefer using public or private transport in your country?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "what you think would be the perfect holiday",
        "bullets": [
            "where it would be",
            "what activities you would do",
            "how long it would last",
        ],
        "follow_up": "and explain why this holiday would be perfect for you",
    },
}

PART3_CONTENT = {
    "part": 3,
    "topics": ["Tourism", "Holidays"],
    "questions": [
        "What are some of the best places in your country for a tourist to visit?",
        "What are some of the advantages and disadvantages that tourism brings "
        "to an area?",
        "Could you compare the tourism industry in your country today with that "
        "of 50 years ago?",
        "What factors do you think could limit the expansion of tourism in the "
        "future?",
        "Why do you think people need holidays?",
        "How much holiday a year do you think a person needs?",
        "How have people's expectations about holidays changed over the last "
        "50 years?",
        "How do you think holidays will change in the next 50 years?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 — Studying English, transport"),
    (31, PART2_CONTENT, "Part 2 — The perfect holiday"),
    (32, PART3_CONTENT, "Part 3 — Tourism and holidays"),
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
