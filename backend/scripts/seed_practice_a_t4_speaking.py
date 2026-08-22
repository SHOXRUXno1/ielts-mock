"""Seed Practice Set A Test 4 Speaking, Parts 1-3.

Part 1: where the candidate lives, then Parks, then Free Time.
Part 2: describe one of your good friends.
Part 3: Family and Friends, then Living with Friends.

The paper offers two topics in Parts 1 and 3; both are kept, which is how a real
examiner works through the part.

Idempotent: each part section is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t4_speaking.py
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

TEST_NUMBER = 4

PART1_CONTENT = {
    "part": 1,
    "topic": "Parks / Free Time",
    "questions": [
        "Describe the house or flat/apartment in which you live at the moment.",
        "Do you think it is better to live in a house or a flat/apartment?",
        "What are the advantages and disadvantages of having a garden?",
        "Do you visit parks? [Why/Why not?]",
        "Do you think parks are important for towns and cities? [Why/Why not?]",
        "Do you think that parks should be free or that people should pay to "
        "use them?",
        "What are some of the disadvantages of parks in a town or city?",
        "Do you have much free time in your life? [Why/Why not?]",
        "What do you like doing in your free time?",
        "What free time activities do you particularly dislike?",
        "How much free time do you think a person should have every day?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "one of your good friends",
        "bullets": [
            "where you met",
            "what this person does",
            "what things you do together",
        ],
        "follow_up": "and why you particularly like this person",
    },
}

PART3_CONTENT = {
    "part": 3,
    "topics": ["Family and Friends", "Living with Friends"],
    "questions": [
        "Do you prefer spending time with your family or with your friends? [Why?]",
        "Can you compare the activities that you do with your friends and your "
        "family?",
        "Do you think it is important for your family and friends to like each "
        "other?",
        "Can you compare the relationships that you have with friends and the "
        "ones you have with family?",
        "Do you live alone, with friends or with family? [Why?]",
        "What are some of the advantages of living with friends?",
        "What are some of the disadvantages of living with friends?",
        "What are some of things that can break a friendship?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 — Where you live, parks, free time"),
    (31, PART2_CONTENT, "Part 2 — One of your good friends"),
    (32, PART3_CONTENT, "Part 3 — Family and friends, living with friends"),
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
