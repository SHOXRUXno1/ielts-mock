"""Seed Reading Passage 3 matching_information Q27-29 into IELTS 11."""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section
from app.models.test import Test

TEST_ID = uuid.UUID("1f4988f6-52d0-49d7-881e-3be2032f9429")
PASSAGE3_ID = uuid.UUID("9c78a0d6-ada1-434b-b1cb-7398e6fe4ad8")

INSTRUCTION = (
    "Reading Passage 3 has eight paragraphs, A-H.\n"
    "Which paragraph contains the following information?\n"
    "Choose the correct letter, A-H, in boxes 27-29 on your answer sheet."
)

# Cambridge IELTS 11 Reading Test 1 Passage 3 — Reducing the Effects of Climate Change
QUESTIONS: list[dict] = [
    {
        "order": 27,
        "question": "mention of a geo-engineering project based on an earlier natural phenomenon",
        "correct": "D",
    },
    {
        "order": 28,
        "question": "an example of a successful use of geo-engineering",
        "correct": "B",
    },
    {
        "order": 29,
        "question": "a common definition of geo-engineering",
        "correct": "A",
    },
]

OPTIONS = [f"{letter}" for letter in "ABCDEFGH"]


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")

        section = await db.get(
            Section,
            PASSAGE3_ID,
            options=[
                selectinload(Section.question_groups).selectinload(
                    QuestionGroup.questions
                )
            ],
        )
        if section is None:
            raise SystemExit(f"Section {PASSAGE3_ID} not found")

        print(f"Test: {test.title}")
        print(f"Passage: {section.title} ({section.id})")

        existing = [
            g
            for g in (section.question_groups or [])
            if str(getattr(g.question_type, "value", g.question_type))
            == "matching_information"
        ]
        for g in existing:
            print(f"Deleting existing MI group {g.id}")
            await db.delete(g)
        if existing:
            await db.flush()

        remaining = await db.execute(
            select(QuestionGroup).where(QuestionGroup.section_id == PASSAGE3_ID)
        )
        max_group_order = max((g.order for g in remaining.scalars().all()), default=0)

        group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PASSAGE3_ID,
            order=max_group_order + 1,
            question_type=QuestionType.MATCHING_INFORMATION.value,
            instruction=INSTRUCTION,
            subtitle="List of Paragraphs",
            options_shared={"options": OPTIONS},
        )
        db.add(group)
        await db.flush()

        for item in QUESTIONS:
            q = Question(
                id=uuid.uuid4(),
                section_id=PASSAGE3_ID,
                question_group_id=group.id,
                order=item["order"],
                question_type=QuestionType.MATCHING_INFORMATION,
                content={"question": item["question"]},
                answer_key={"correct": item["correct"]},
            )
            db.add(q)
            print(f"  Q{item['order']} -> {item['correct']}")

        await db.commit()
        print(f"\nDone. Group {group.id} with 3 matching_information questions seeded.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
