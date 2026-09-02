"""Seed Practice Set D Test 6 Speaking, Parts 1-3.

Wording is taken from the printed paper (p.170). Examiner admin
questions are omitted. Teaching tip strips are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_d_t6_speaking.py
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

TEST_NUMBER = 6

PART1_CONTENT = {
    "part": 1,
    "topic": "Hobbies",
    "questions": [
        "What hobbies and interests are popular in your country?",
        "Which hobbies or interests do you enjoy?",
        "Which hobbies or interests did you have when you were "
        "a child?",
        "Do you think parents should encourage their children to "
        "have a hobby or interest?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "the job you most like to have",
        "bullets": [
            "what this job would be",
            "where you would work",
            "which qualifications you would need",
        ],
        "follow_up": "and explain why you would like to have "
        "this job most",
    },
    "rounding_off": [],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Jobs and employment",
    ],
    "questions": [
        "Which jobs are most respected in your country?",
        "Do you think schools provide enough advice and support "
        "about future careers?",
        "What changes have there been in recent years in "
        "employment in your country?",
        "Do you agree that pay for a job should reflect the "
        "level of contribution to community the job makes?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 \u2014 Hobbies"),
    (
        31,
        PART2_CONTENT,
        "Part 2 \u2014 Describe the job you most like to have",
    ),
    (32, PART3_CONTENT, "Part 3 \u2014 Jobs and employment"),
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
