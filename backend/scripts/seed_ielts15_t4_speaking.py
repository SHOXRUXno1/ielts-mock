"""Seed Cambridge IELTS 15 Test 4 Speaking Parts 1–3.

Usage:
    python /app/scripts/seed_ielts15_t4_speaking.py
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

TEST_ID = uuid.UUID("8e84227c-abde-41f9-ab36-7ea51527b7e6")
PROTECTED_TEST_IDS = {
    uuid.UUID("6528e947-1883-4318-bca0-8fb9face3590"),
    uuid.UUID("6074d5f2-70b8-4f31-9b59-10f861a3eadf"),
    uuid.UUID("3b766b14-d188-4c81-814f-77fadff4e3fa"),
}

PART1_CONTENT = {
    "part": 1,
    "topic": "Jewellery",
    "questions": [
        "How often do you wear jewellery? [Why/Why not?]",
        "What type of jewellery do you like best? [Why/Why not?]",
        "When do people like to give jewellery in your country? [Why?]",
        "Have you ever given jewellery to someone as a gift? [Why/Why not?]",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "an interesting TV programme you watched about a science topic",
        "bullets": [
            "what science topic this TV programme was about",
            "when you saw this TV programme",
            "what you learnt from this TV programme about a science topic",
        ],
        "follow_up": "why you found this TV programme interesting",
    },
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Science and the public",
        "Scientific discoveries",
    ],
    "questions": [
        "How interested are most people in your country in science?",
        "Why do you think children today might be better at science than their parents?",
        "How do you suggest the public can learn more about scientific developments?",
        "What do you think are the most important scientific discoveries in the last 100 years?",
        "Do you agree or disagree that there are no more major scientific discoveries left to make?",
        "Who should pay for scientific research – governments or private companies?",
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
    title: str,
) -> None:
    section.title = title
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
    if TEST_ID in PROTECTED_TEST_IDS:
        raise SystemExit(f"Refusing to seed into protected test {TEST_ID}")

    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")
        if test.id in PROTECTED_TEST_IDS:
            raise SystemExit(f"Refusing to seed into protected test {test.id}")

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

        print(f"Test: {test.title} ({test.id})")
        print("Part 1 — Jewellery")
        await seed_part(db, parts[0], PART1_CONTENT, "Part 1", "Part 1 — Jewellery")
        print("Part 2 — An interesting TV programme about a science topic")
        await seed_part(
            db,
            parts[1],
            PART2_CONTENT,
            "Part 2",
            "Part 2 — An interesting TV programme you watched about a science topic",
        )
        print("Part 3 — Science and the public / Scientific discoveries")
        await seed_part(
            db,
            parts[2],
            PART3_CONTENT,
            "Part 3",
            "Part 3 — Science and the public & Scientific discoveries",
        )

        await db.commit()
        print("\nDone. Speaking Parts 1–3 seeded into IELTS 15 Test 4. Unpublished.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
