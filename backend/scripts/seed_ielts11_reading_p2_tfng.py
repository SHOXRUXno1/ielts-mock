"""Seed Reading Passage 2 true_false_ng Q14-19 (The Falkirk Wheel) into IELTS 11."""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section
from app.models.test import Test

TEST_ID = uuid.UUID("1f4988f6-52d0-49d7-881e-3be2032f9429")
PASSAGE2_ID = uuid.UUID("94877ee7-e06b-4f82-b799-b73d77884fae")
GROUP_ID = uuid.UUID("774659e7-9eb7-4491-901b-eff62b5a7b48")

INSTRUCTION = (
    "Do the following statements agree with the information given in Reading Passage 2?\n"
    "In boxes 14-19 on your answer sheet, choose"
)

# Cambridge IELTS 11 Reading Test 1 Passage 2 — The Falkirk Wheel
QUESTIONS: list[dict] = [
    {
        "order": 14,
        "statement": (
            "The Falkirk Wheel has linked the Forth & Clyde Canal with the "
            "Union Canal for the first time in their history."
        ),
        "correct": "False",
    },
    {
        "order": 15,
        "statement": "There was some opposition to the design of the Falkirk Wheel at first.",
        "correct": "Not Given",
    },
    {
        "order": 16,
        "statement": (
            "The Falkirk Wheel was initially put together at the location "
            "where its components were manufactured."
        ),
        "correct": "True",
    },
    {
        "order": 17,
        "statement": (
            "The Falkirk Wheel is the only boat lift in the world which has "
            "steel sections bolted together by hand."
        ),
        "correct": "Not Given",
    },
    {
        "order": 18,
        "statement": (
            "The weight of the gondolas varies according to the size of boat being carried."
        ),
        "correct": "False",
    },
    {
        "order": 19,
        "statement": (
            "The construction of the Falkirk Wheel site took into account "
            "the presence of a nearby ancient monument."
        ),
        "correct": "True",
    },
]


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")

        group = await db.get(QuestionGroup, GROUP_ID)
        if group is None:
            raise SystemExit(f"Group {GROUP_ID} not found")

        section = await db.get(Section, PASSAGE2_ID)
        if section is None:
            raise SystemExit(f"Section {PASSAGE2_ID} not found")

        print(f"Test: {test.title}")
        print(f"Passage: {section.title} ({section.id})")
        print(f"Group: {group.id}")

        existing = await db.execute(
            select(Question).where(Question.question_group_id == GROUP_ID)
        )
        for q in existing.scalars().all():
            print(f"Deleting existing question order={q.order}")
            await db.delete(q)
        await db.flush()

        group.instruction = INSTRUCTION
        group.subtitle = None
        group.question_type = QuestionType.TRUE_FALSE_NG.value

        for item in QUESTIONS:
            q = Question(
                id=uuid.uuid4(),
                section_id=PASSAGE2_ID,
                question_group_id=GROUP_ID,
                order=item["order"],
                question_type=QuestionType.TRUE_FALSE_NG,
                content={"statement": item["statement"]},
                answer_key={"correct": item["correct"]},
            )
            db.add(q)
            print(f"  Q{item['order']} -> {item['correct']}")

        await db.commit()
        print("\nDone. 6 TFNG questions seeded into Passage 2.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
