"""Seed Cambridge IELTS 15 Test 2 Speaking Parts 1–3.

Usage:
    python /app/scripts/seed_ielts15_t2_speaking.py
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

TEST_ID = uuid.UUID("6074d5f2-70b8-4f31-9b59-10f861a3eadf")

PART1_CONTENT = {
    "part": 1,
    "topic": "Languages",
    "questions": [
        "How many languages can you speak? [Why/Why not?]",
        "How useful will English be to you in your future? [Why/Why not?]",
        "What do you remember about learning languages at school? [Why/Why not?]",
        "What do you think would be the hardest language for you to learn? [Why?]",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a website that you bought something from",
        "bullets": [
            "what the website is",
            "what you bought from this website",
            "how satisfied you were with what you bought",
        ],
        "follow_up": "what you liked or disliked about using this website",
    },
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Shopping online",
        "The culture of consumerism",
    ],
    "questions": [
        "What kinds of things do people in your country often buy from online shops?",
        "Why do you think online shopping has become so popular nowadays?",
        "What are some possible disadvantages of buying things from online shops?",
        "Why do many people today keep buying things which they do not need?",
        "Do you believe the benefits of a consumer society outweigh the disadvantages?",
        "How possible is it to avoid the culture of consumerism?",
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

        print(f"Test: {test.title} ({test.id})")
        print("Part 1 — Languages")
        await seed_part(db, parts[0], PART1_CONTENT, "Part 1", "Part 1 — Languages")
        print("Part 2 — A website that you bought something from")
        await seed_part(
            db,
            parts[1],
            PART2_CONTENT,
            "Part 2",
            "Part 2 — A website that you bought something from",
        )
        print("Part 3 — Shopping online / The culture of consumerism")
        await seed_part(
            db,
            parts[2],
            PART3_CONTENT,
            "Part 3",
            "Part 3 — Shopping online & consumerism",
        )

        await db.commit()
        print("\nDone. Speaking Parts 1–3 seeded into IELTS 15 Test 2.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
