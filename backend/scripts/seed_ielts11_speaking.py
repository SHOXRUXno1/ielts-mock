"""Seed IELTS 11 Speaking Parts 1–3 (Cambridge Academic Test 11)."""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.question import Question, QuestionType
from app.models.section import Section
from app.models.test import Test

TEST_ID = uuid.UUID("1f4988f6-52d0-49d7-881e-3be2032f9429")

PART1_ID = uuid.UUID("bb45d2cb-ab94-4a15-a20f-d4ae0d2d6133")
PART2_ID = uuid.UUID("1f6e43f4-bef3-471f-a826-05e28eb30218")
PART3_ID = uuid.UUID("ad41b982-074a-40bb-8adf-72783869b955")

# JumpInto / Cambridge IELTS 11 Academic Speaking
PART1_CONTENT = {
    "part": 1,
    "topic": "Food and cooking",
    "questions": [
        "What sorts of food do you like eating most? [Why?]",
        "Who normally does the cooking in your home? [Why/Why not?]",
        "Do you watch cookery programmes on TV? [Why/Why not?]",
        "In general, do you prefer eating out or eating at home? [Why?]",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a house/apartment that someone you know lives in",
        "bullets": [
            "whose house/apartment this is",
            "where the house/apartment is",
            "what it looks like inside",
        ],
        "follow_up": "what you like or dislike about this person's house/apartment",
    },
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Different types of home",
        "Finding a place to live",
    ],
    "questions": [
        "What kinds of home are most popular in your country? Why is this?",
        "What do you think are the advantages of living in a house rather than an apartment?",
        "Do you think that everyone would like to live in a larger home? Why is that?",
        "How easy is it to find a place to live in your country?",
        "Do you think it's better to rent or to buy a place to live in? Why?",
        "Do you agree that there is a right age for young adults to stop living with their parents? Why is that?",
    ],
}


async def seed_part(
    db: AsyncSession,
    section_id: uuid.UUID,
    content: dict,
    label: str,
) -> None:
    section = await db.get(
        Section,
        section_id,
        options=[selectinload(Section.questions)],
    )
    if section is None:
        raise SystemExit(f"Section {section_id} not found ({label})")

    existing = [
        q
        for q in (section.questions or [])
        if str(getattr(q.question_type, "value", q.question_type)) == "speaking_part"
    ]
    for q in existing:
        print(f"  Deleting existing {label} question {q.id}")
        await db.delete(q)
    if existing:
        await db.flush()

    q = Question(
        id=uuid.uuid4(),
        section_id=section_id,
        question_group_id=None,
        order=1,
        question_type=QuestionType.SPEAKING_PART,
        content=content,
        answer_key=None,
    )
    db.add(q)
    print(f"  Seeded {label} -> question {q.id}")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")

        print(f"Test: {test.title}")
        print("Part 1 — Food and cooking")
        await seed_part(db, PART1_ID, PART1_CONTENT, "Part 1")
        print("Part 2 — Cue card")
        await seed_part(db, PART2_ID, PART2_CONTENT, "Part 2")
        print("Part 3 — Discussion")
        await seed_part(db, PART3_ID, PART3_CONTENT, "Part 3")

        await db.commit()
        print("\nDone. Speaking Parts 1–3 seeded into IELTS 11.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
