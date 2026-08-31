"""Seed Practice Set B Test 6 Speaking, Parts 1-3.

Wording is taken from the printed paper (p.142). Examiner admin questions
(name / nationality) are omitted — the platform already identifies the student.
The teaching tip strips on p.142 are not part of the exam and are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t6_speaking.py
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
from seed_practice_b_common import clear_section, get_section, get_test  # noqa: E402

TEST_NUMBER = 6

PART1_CONTENT = {
    "part": 1,
    "topic": "Your city and music",
    "questions": [
        "Tell me about the town or city you live in now.",
        "How long have you lived in this city?",
        "Do tourists visit your city? Why / Why not?",
        "What places do you think tourists should see in your city?",
        "What is the best way for tourists to travel around your city? Why?",
        "What kind of music do you prefer? Why?",
        "Have you ever been to a music concert? Why / Why not?",
        "Why do you think music is important to people?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a TV or radio programme you enjoyed when you were a child",
        "bullets": [
            "what the programme was about",
            "when it was on",
            "where you watched or listened to it",
        ],
        "follow_up": (
            "and explain why you enjoyed this programme when you were a child"
        ),
    },
    "rounding_off": [
        "Would you still like this programme today?",
        "Did your friends enjoy this programme too?",
    ],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "TV and radio in your country",
        "The effects of TV",
        "Developments in programming",
    ],
    "questions": [
        "In your country, which do people prefer: watching TV or listening "
        "to radio? Why?",
        "What kind of programmes are most popular?",
        "Do men and women tend to like the same kind of programmes? "
        "Why / Why not?",
        "Some people think that watching TV can be a negative influence. "
        "Would you agree?",
        "What benefits can TV bring people?",
        "What priorities do you think TV stations should have?",
        "What kind of 'interactive' programmes are there in your country?",
        "Are these a good or a bad development? Why?",
        "What kind of programmes will there be in the future, do you think?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 — Your city and music"),
    (
        31,
        PART2_CONTENT,
        "Part 2 — A TV or radio programme you enjoyed as a child",
    ),
    (32, PART3_CONTENT, "Part 3 — TV, radio and programming"),
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
