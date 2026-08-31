"""Seed Practice Set C Test 1 Speaking, Parts 1-3.

Wording is taken from the printed paper (p.31). Examiner admin questions
(name / nationality) are omitted — the platform already identifies the student.
The teaching tip strips on pp.30-31 are not part of the exam and are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t1_speaking.py
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
from seed_practice_c_common import clear_section, get_section, get_test  # noqa: E402

TEST_NUMBER = 1

PART1_CONTENT = {
    "part": 1,
    "topic": "Your country and your family",
    "questions": [
        "What's the weather like in your country?",
        "Which time of year do you think is best in your country? Why?",
        "Have you visited many different parts of your country? Why / Why not?",
        "Do you share a house with any of your family? Who?",
        "Do most people in your family live in the same town or village?",
        "When did you last have a family party?",
        "Which person in your family are you most similar to? How?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": (
            "a place in another part of the world that you would love to "
            "visit in the future"
        ),
        "bullets": [
            "what you know about the place",
            "how you know about it",
            "how you would go there",
        ],
        "follow_up": "and explain why you would love to visit that place",
    },
    "rounding_off": [
        "Who would you go to that place with?",
        "Do you enjoy travelling generally?",
    ],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "TV programmes about other places",
        "Visiting other countries",
        "The tourism industry",
    ],
    "questions": [
        "What kinds of TV programme about different places are most popular "
        "in your country?",
        "Can people learn more about geography from TV than they can from "
        "books? Why / Why not?",
        "Do you think TV programmes about different places encourage people "
        "to travel themselves? Why / Why not?",
        "For what reasons do you think international travel has increased in "
        "recent years?",
        "Some people say it's important for people to find out about another "
        "country before they visit it. Do you agree?",
        "How useful is it for people to understand the language of the "
        "countries they visit? Why?",
        "Does tourism play a big part in the economy of your country? How?",
        "What kinds of unpredictable factors can have a negative effect on "
        "the tourism industry?",
        "In the future, what kinds of development might there be in the "
        "tourism industry?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 — Your country and your family"),
    (
        31,
        PART2_CONTENT,
        "Part 2 — A place in another part of the world you would love to visit",
    ),
    (32, PART3_CONTENT, "Part 3 — Travel, other countries and tourism"),
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
    print("\nDone. Speaking seeded (Parts 1–3).")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
