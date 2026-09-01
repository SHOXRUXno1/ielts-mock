"""Seed Practice Set C Test 6 Speaking, Parts 1-3.

Wording is taken from the printed paper (p.132). Examiner admin questions
(name / nationality) are omitted — the platform already identifies the student.
The teaching tip strips are not part of the exam and are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t6_speaking.py
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

TEST_NUMBER = 6

PART1_CONTENT = {
    "part": 1,
    "topic": "Where you live and holidays",
    "questions": [
        "Do you live near here?",
        "Do you live in a house or an apartment?",
        "How long have you lived there?",
        "Do you like where you are living now? Why / Why not?",
        "How often do you get holiday from work/college?",
        "Do you usually stay at home when you have a holiday, or do you "
        "go somewhere? Why / Why not?",
        "What did you do the last time you had a holiday?",
        "Do you wish you had more holidays? Why / Why not?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a sports match which you saw and which you found enjoyable",
        "bullets": [
            "what the sport was",
            "who was playing in this game",
            "where you watched it",
        ],
        "follow_up": "and explain why you enjoyed watching the match so much",
    },
    "rounding_off": [
        "Do you often watch sport?",
        "Do you do a lot of sport?",
    ],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Young people doing sports",
        "Sports on TV",
        "International sports competitions",
    ],
    "questions": [
        "What sports do most young people in your country enjoy doing?",
        "What are the main benefits for young people of learning to play "
        "different sports?",
        "Can you suggest some ways to encourage young people to play "
        "more sport?",
        "What kinds of sport do people in your country most often watch "
        "on TV? Why?",
        "What do you think are the disadvantages of having a lot of "
        "coverage of sports on TV?",
        "How do you think the broadcasting of sports on TV will change "
        "in the next 20 years?",
        "Why do you think international sports competitions (like the "
        "Football World Cup) are so popular?",
        "What are the advantages and disadvantages to a country when it "
        "hosts a major international sports competition?",
        "What should governments invest more in: helping their top sports "
        "people to win international competitions, or in promoting sport "
        "for everyone? Why?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 \u2014 Where you live and holidays"),
    (
        31,
        PART2_CONTENT,
        "Part 2 \u2014 Describe a sports match which you saw and "
        "found enjoyable",
    ),
    (
        32,
        PART3_CONTENT,
        "Part 3 \u2014 Young people and sport, sports on TV and "
        "international competitions",
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
