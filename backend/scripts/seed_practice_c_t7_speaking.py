"""Seed Practice Set C Test 7 Speaking, Parts 1-3.

Wording is taken from the printed paper (p.152). Examiner admin questions
(name / nationality) are omitted — the platform already identifies the student.
The teaching tip strips are not part of the exam and are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t7_speaking.py
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

TEST_NUMBER = 7

PART1_CONTENT = {
    "part": 1,
    "topic": "Your country and shops",
    "questions": [
        "Which part of the country are you from?",
        "Has your family always lived there?",
        "Do you like living in your country? Why / Why not?",
        "Is your country changing a lot? How?",
        "Do you enjoy going shopping? Why?",
        "In your country, what time do shops generally open?",
        "What would you recommend visitors to your country to buy?",
        "How are shops changing in your country? Why?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": (
            "an occasion when you met someone you hadn\u2019t seen for "
            "several years"
        ),
        "bullets": [
            "how and when you met the person",
            "who the person was",
            "how long it was since you had last seen him/her",
        ],
        "follow_up": (
            "and explain how you felt about meeting this person again"
        ),
    },
    "rounding_off": [
        "Did you recognise him/her straight away?",
        "Had he/she changed a lot?",
    ],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Keeping in touch",
        "Change with age",
        "Long-term relationships",
    ],
    "questions": [
        "In what different ways can people keep in touch with each other?",
        "How important do you think it is to keep in touch with friends? "
        "Why / Why not?",
        "Which way of keeping in touch do you think is most popular with "
        "young people?",
        "What are the reasons why people change as they grow older?",
        "Why do you think some people change more than others?",
        "At about what age do you think people change the most? "
        "Why / Why not?",
        "How valuable do you think long-term friendships are compared "
        "with new relationships? Why / Why not?",
        "Do you agree that maintaining long-term relationships sometimes "
        "requires effort? Why / Why not?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 \u2014 Your country and shops"),
    (
        31,
        PART2_CONTENT,
        "Part 2 \u2014 An occasion when you met someone you hadn\u2019t "
        "seen for several years",
    ),
    (
        32,
        PART3_CONTENT,
        "Part 3 \u2014 Keeping in touch, change with age, "
        "long-term relationships",
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
