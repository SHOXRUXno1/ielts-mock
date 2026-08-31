"""Seed Practice Set C Test 2 Speaking, Parts 1-3.

Wording is taken from the printed paper (p.55). Examiner admin questions
(name / nationality) are omitted — the platform already identifies the student.
The teaching tip strips on pp.54-55 are not part of the exam and are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t2_speaking.py
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

TEST_NUMBER = 2

PART1_CONTENT = {
    "part": 1,
    "topic": "Free time and clothes",
    "questions": [
        "How much free time do you normally have?",
        "What do you usually do in your free time?",
        "Who do you spend your free time with?",
        "Do you wish you had more free time? Why / Why not?",
        "Is it important to you to wear clothes that are comfortable?",
        "Are you interested in fashion? Why / Why not?",
        "Were you interested in clothes when you were a child?",
        "What are your favourite clothes like now?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a TV series which you enjoy watching",
        "bullets": [
            "what the series is about",
            "who presents it / acts in it",
            "how often it is on",
        ],
        "follow_up": "and explain why you enjoy watching the series so much",
    },
    "rounding_off": [
        "Is this series popular with many other people you know?",
        "Do you watch TV often?",
    ],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Foreign TV programmes",
        "Children and TV",
        "Changes in the media",
    ],
    "questions": [
        "What kind of foreign TV programmes are popular in your country?",
        "What are the advantages of having foreign-made programmes on TV?",
        "Some people think governments should control the number of "
        "foreign-made TV programmes being shown. Do you agree? Why?",
        "What do you think are the qualities of a good children's TV "
        "programme?",
        "What are the educational benefits of children watching TV?",
        "Many people think adults should influence what children watch. "
        "Do you agree? Why?",
        "What do you think are the advantages and disadvantages of having "
        "TV broadcast 24 hours a day?",
        "In what ways have advances in technology influenced the way "
        "people watch TV?",
        "What changes do you think will occur in broadcast media in the "
        "next 20 years?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 — Free time and clothes"),
    (31, PART2_CONTENT, "Part 2 — A TV series which you enjoy watching"),
    (
        32,
        PART3_CONTENT,
        "Part 3 — Foreign TV, children and TV, and changes in the media",
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
    print("\nDone. Speaking seeded (Parts 1–3).")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
