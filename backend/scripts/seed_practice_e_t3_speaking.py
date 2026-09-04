"""Seed Practice Set E Test 3 Speaking, Parts 1-3.

Source: Peter May Oxford IELTS Practice Tests, Test 3 (pp.95-96).
Exam questions only — no "Improve your skills" exercises, no
strategy boxes.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_e_t3_speaking.py
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

TEST_NUMBER = 3

PART1_CONTENT = {
    "part": 1,
    "topic": "School days / Going abroad / Entertainment",
    "questions": [
        "What do you remember about your first school, when you were a child?",
        "In what ways did life at school change as you became older?",
        "What was your favourite subject? Why?",
        "What experience do you have of travelling to other countries?",
        "Which country would you especially like to visit? Why?",
        "What are the best ways to get to know a country?",
        "What are the biggest cultural differences between your country "
        "and English-speaking countries?",
        "What sort of television programmes do you like watching?",
        "How has television in your country changed in recent years?",
        "Which do you prefer: the cinema, the theatre, or live music? Why?",
        "Tell me about a popular form of public entertainment in your country.",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a place that has a special meaning to you",
        "bullets": [
            "what kind of place it is and where it is",
            "what it looks like",
            "what sounds you associate with it",
        ],
        "follow_up": "and explain why you particularly like the place",
    },
    "rounding_off": [
        "When do you think you will next go there?",
        "How would you feel if the place changed in a significant way?",
    ],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Leaving the family home",
        "Moving from place to place",
        "Growing cities",
    ],
    "questions": [
        "Why do many people leave home when they are still quite young?",
        "What personal qualities do you feel are required for a "
        "young person to live on their own?",
        "In many countries there has been large-scale migration from "
        "the countryside to the cities. Do you think this is positive "
        "or negative?",
        "Do you think that the possibility of working from home via "
        "the Internet will lead to many people going back to the "
        "countryside?",
        "In what ways do the new megacities of Asia, Africa, and "
        "South America differ from older ones such as London or "
        "New York?",
        "Should there be a limit on the size of cities?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 \u2014 School days, going abroad, entertainment"),
    (
        31,
        PART2_CONTENT,
        "Part 2 \u2014 Describe a place with special meaning",
    ),
    (
        32,
        PART3_CONTENT,
        "Part 3 \u2014 Leaving home, migration, growing cities",
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
