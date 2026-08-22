"""Seed Cambridge IELTS 15 Test 1 Speaking Parts 1–3.

Usage (prod container):
    python /tmp/seed_ielts15_t1_speaking.py
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section, SectionType
from app.models.test import Test

TEST_ID = uuid.UUID("6528e947-1883-4318-bca0-8fb9face3590")

PART1_CONTENT = {
    "part": 1,
    "topic": "Email",
    "questions": [
        "What kinds of emails do you receive about your work or studies?",
        "Do you prefer to email, phone or text your friends? [Why?]",
        "Do you reply to emails and messages as soon as you receive them? [Why/Why not?]",
        "Are you happy to receive emails that are advertising things? [Why/Why not?]",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a hotel that you know",
        "bullets": [
            "where this hotel is",
            "what this hotel looks like",
            "what facilities this hotel has",
        ],
        "follow_up": "whether you think this is a nice hotel to stay in",
    },
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Staying in hotels",
        "Working in a hotel",
    ],
    "questions": [
        "What things are important when people are choosing a hotel?",
        "Why do some people not like staying in hotels?",
        "Do you think staying in a luxury hotel is a waste of money?",
        "Do you think hotel work is a good career for life?",
        "How does working in a big hotel compare with working in a small hotel?",
        "What skills are needed to be a successful hotel manager?",
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
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
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
        print("Part 1 — Email")
        await seed_part(db, parts[0], PART1_CONTENT, "Part 1")
        print("Part 2 — A hotel that you know")
        await seed_part(db, parts[1], PART2_CONTENT, "Part 2")
        print("Part 3 — Staying in hotels / Working in a hotel")
        await seed_part(db, parts[2], PART3_CONTENT, "Part 3")

        await db.commit()
        print("\nDone. Speaking Parts 1–3 seeded into IELTS 15 Test 1.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
