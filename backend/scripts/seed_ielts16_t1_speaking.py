"""Seed IELTS 16 Test 1 Speaking Parts 1–3 (Jumpinto / Cambridge prompts).

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_ielts16_t1_speaking.py
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

TEST_ID = uuid.UUID("4cdab44f-db90-4122-a02b-d7df41fc400a")

PART1_CONTENT = {
    "part": 1,
    "topic": "People you study/work with",
    "questions": [
        "Who do you spend most time studying/working with? [Why?]",
        "What kinds of things do you study/work on with other people? [Why?]",
        "Are there times when you study/work better by yourself? [Why/Why not?]",
        "Is it important to like the people you study/work with? [Why/Why not?]",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a tourist attraction you enjoyed visiting",
        "bullets": [
            "what this tourist attraction is",
            "when and why you visited it",
            "what you did there",
        ],
        "follow_up": "why you enjoyed visiting this tourist attraction",
    },
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Different kinds of tourist attractions",
        "The importance of international tourism",
    ],
    "questions": [
        "What are the most popular tourist attractions in your country?",
        (
            "How do the types of tourist attractions that younger people "
            "like to visit compare with those that older people like to visit?"
        ),
        (
            "Do you agree that some tourist attractions "
            "(e.g. national museums/galleries) should be free to visit?"
        ),
        "Why is tourism important to a country?",
        "What are the benefits to individuals of visiting another country as tourists?",
        (
            "How necessary is it for tourists to learn the language "
            "of the country they're visiting?"
        ),
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
        print("Part 1 — People you study/work with")
        await seed_part(db, parts[0], PART1_CONTENT, "Part 1")
        print("Part 2 — Tourist attraction cue card")
        await seed_part(db, parts[1], PART2_CONTENT, "Part 2")
        print("Part 3 — Tourist attractions / international tourism")
        await seed_part(db, parts[2], PART3_CONTENT, "Part 3")

        await db.commit()
        print("\nDone. Speaking Parts 1–3 seeded into Ielts 16.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
