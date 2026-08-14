"""Seed Speaking Parts 1–3 for Cambridge IELTS 9 – Test 4 (Jumpinto prompts)."""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload, sessionmaker

from app.core.config import settings
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section, SectionType
from app.models.test import Test

TEST_ID = uuid.UUID("9a8f1a55-c58f-4a86-94c6-677b74ef9eba")

PART1_CONTENT = {
    "part": 1,
    "topic": "Cafés",
    "questions": [
        "Do you have a favourite café? [Why/Why not?]",
        "Do you often go to cafés by yourself? [Why/Why not?]",
        "What do you think helps to make a café very popular? [Why?]",
        "Why do some people prefer cafés that are part of large chains, rather than small, local cafés?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a place you visited that has beautiful views",
        "bullets": [
            "where this place is",
            "when and why you visited it",
            "what views you can see from this place",
        ],
        "follow_up": "why you think these views are so beautiful",
    },
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "The beauty industry",
        "Beauty and culture",
    ],
    "questions": [
        "Do you agree that most beauty products are a waste of money?",
        "How does the beauty industry advertise its products so successfully?",
        "What do you think of the view that beauty products should not be advertised to children?",
        "Why do many people equate youth with beauty?",
        "Do you think that being beautiful could affect a person's success in life?",
        "Why might society's ideas about beauty change over time?",
    ],
}


async def _ensure_group(db: AsyncSession, section_id: uuid.UUID) -> uuid.UUID:
    existing = await db.execute(
        select(QuestionGroup)
        .where(
            QuestionGroup.section_id == section_id,
            QuestionGroup.question_type == QuestionType.SPEAKING_PART,
        )
        .order_by(QuestionGroup.order.desc())
        .limit(1)
    )
    group = existing.scalar_one_or_none()
    if group is not None:
        return group.id

    max_result = await db.execute(
        select(func.coalesce(func.max(QuestionGroup.order), 0)).where(
            QuestionGroup.section_id == section_id
        )
    )
    next_order = (max_result.scalar() or 0) + 1
    group = QuestionGroup(
        section_id=section_id,
        order=next_order,
        question_type=QuestionType.SPEAKING_PART,
        instruction="",
        options_shared=None,
    )
    db.add(group)
    await db.flush()
    return group.id


async def seed_part(
    db: AsyncSession,
    section: Section,
    content: dict,
    label: str,
) -> None:
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

    group_id = await _ensure_group(db, section.id)
    q = Question(
        id=uuid.uuid4(),
        section_id=section.id,
        question_group_id=group_id,
        order=1,
        question_type=QuestionType.SPEAKING_PART,
        content=content,
        answer_key=None,
    )
    db.add(q)
    print(f"  Seeded {label} -> question {q.id} (section {section.id})")


async def main() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")

        result = await db.execute(
            select(Section)
            .where(
                Section.test_id == TEST_ID,
                Section.type == SectionType.SPEAKING,
            )
            .order_by(Section.order)
            .options(selectinload(Section.questions))
        )
        parts = list(result.scalars().all())
        if len(parts) < 3:
            raise SystemExit(f"Expected 3 speaking sections, found {len(parts)}")

        print(f"Test: {test.title}")
        print("Part 1 - Cafes")
        await seed_part(db, parts[0], PART1_CONTENT, "Part 1")
        print("Part 2 - Cue card (beautiful views)")
        await seed_part(db, parts[1], PART2_CONTENT, "Part 2")
        print("Part 3 - Beauty industry / Beauty and culture")
        await seed_part(db, parts[2], PART3_CONTENT, "Part 3")

        await db.commit()
        print("\nDone. Speaking Parts 1-3 seeded.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
