"""Seed Practice Set B Test 4 Speaking, Parts 1-3.

Wording is taken from the printed paper (p.108). Examiner admin questions
(name / nationality) are omitted — the platform already identifies the student.
The teaching tip strips on p.108 are not part of the exam and are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t4_speaking.py
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

TEST_NUMBER = 4

PART1_CONTENT = {
    "part": 1,
    "topic": "Hometown and family",
    "questions": [
        "Whereabouts is your home town?",
        "Tell me about the countryside outside your town.",
        "How big is your family?",
        "How often do you spend time together?",
        "What do you enjoy doing as a family?",
        "How do you keep in touch with members of your family?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "something you bought that you were not happy with",
        "bullets": [
            "what you bought",
            "why you were not happy with it",
            "what you did with it",
        ],
        "follow_up": "and explain how you felt about the situation",
    },
    "rounding_off": [
        "Would you buy other things from the same shop / place?",
        "Do you usually enjoy shopping?",
    ],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Products people buy",
        "Protecting consumers",
    ],
    "questions": [
        "Are there more goods available in shops now than in the past? "
        "Why / Why not?",
        "Do people generally prefer to buy products from their own or from "
        "other countries?",
        "What kinds of products are most affected by fashions from other "
        "countries?",
        "Will overseas trends and fashions have more or less impact on what "
        "people buy in the future?",
        "What kind of techniques do advertisers use to persuade people to "
        "buy more?",
        "Who should be responsible for the quality of products: producers, "
        "shops or customers?",
        "How could governments protect the rights of consumers?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 — Hometown and family"),
    (
        31,
        PART2_CONTENT,
        "Part 2 — Something you bought and were unhappy with",
    ),
    (32, PART3_CONTENT, "Part 3 — Products and consumer protection"),
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
