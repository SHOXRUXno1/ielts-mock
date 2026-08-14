"""Seed Reading Passage 1 true_false_ng Q8-13 (Indoor farming) into IELTS 11."""

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
PASSAGE1_ID = uuid.UUID("703d53f0-06f3-47ba-ad1e-abf92d0b0114")

INSTRUCTION = (
    "Do the following statements agree with the information given in Reading Passage?\n"
    "In boxes 8-13 on your answer sheet, choose"
)

# Cambridge IELTS 11 Reading Test 1 Passage 1 — Crop-growing skyscrapers
QUESTIONS: list[dict] = [
    {
        "order": 8,
        "statement": "Methods for predicting the Earth's population have recently changed.",
        "correct": "Not Given",
    },
    {
        "order": 9,
        "statement": "Human beings are responsible for some of the destruction to food-producing land.",
        "correct": "True",
    },
    {
        "order": 10,
        "statement": "The crops produced in vertical farms will depend on the season.",
        "correct": "False",
    },
    {
        "order": 11,
        "statement": "Some damage to food crops is caused by climate change.",
        "correct": "True",
    },
    {
        "order": 12,
        "statement": "Fertilisers will be needed for certain crops in vertical farms.",
        "correct": "False",
    },
    {
        "order": 13,
        "statement": "Vertical farming will make plants less likely to be affected by infectious diseases.",
        "correct": "True",
    },
]


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")

        section = await db.get(
            Section,
            PASSAGE1_ID,
            options=[selectinload(Section.question_groups).selectinload(QuestionGroup.questions)],
        )
        if section is None:
            raise SystemExit(f"Section {PASSAGE1_ID} not found")

        print(f"Test: {test.title}")
        print(f"Passage: {section.title} ({section.id})")

        existing_tfng = [
            g
            for g in (section.question_groups or [])
            if str(getattr(g.question_type, "value", g.question_type)) == "true_false_ng"
        ]
        if existing_tfng:
            for g in existing_tfng:
                print(f"Deleting existing TFNG group {g.id} ({len(g.questions or [])} questions)")
                await db.delete(g)
            await db.flush()

        remaining = await db.execute(
            select(QuestionGroup).where(QuestionGroup.section_id == PASSAGE1_ID)
        )
        remaining_groups = list(remaining.scalars().all())
        max_group_order = max((g.order for g in remaining_groups), default=0)

        group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PASSAGE1_ID,
            order=max_group_order + 1,
            question_type=QuestionType.TRUE_FALSE_NG.value,
            instruction=INSTRUCTION,
            subtitle=None,
            options_shared=None,
        )
        db.add(group)
        await db.flush()

        for item in QUESTIONS:
            q = Question(
                id=uuid.uuid4(),
                section_id=PASSAGE1_ID,
                question_group_id=group.id,
                order=item["order"],
                question_type=QuestionType.TRUE_FALSE_NG,
                content={"statement": item["statement"]},
                answer_key={"correct": item["correct"]},
            )
            db.add(q)
            print(f"  Q{item['order']} -> {item['correct']}")

        await db.commit()
        print(f"\nDone. Group {group.id} with 6 TFNG questions seeded into Passage 1.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
