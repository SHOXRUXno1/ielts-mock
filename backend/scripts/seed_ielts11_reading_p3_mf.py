"""Seed Reading Passage 3 matching_features Q37-40 into IELTS 11."""

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
    "Look at the following statements (Questions 37-40) and the list of scientists below.\n"
    "Match each statement with the correct scientist, A-D.\n"
    "Write the correct letter, A-D, in boxes 37-40 on your answer sheet.\n"
    "NB You may use any letter more than once."
)

OPTIONS = [
    "A. Roger Angel",
    "B. Phil Rasch",
    "C. Dan Lunt",
    "D. Martin Sommerkorn",
]

# Cambridge IELTS 11 Reading Test 1 Passage 3
QUESTIONS: list[dict] = [
    {
        "order": 37,
        "question": "The effects of geo-engineering may not be long-lasting.",
        "correct": "B",
    },
    {
        "order": 38,
        "question": "Geo-engineering is a topic worth exploring.",
        "correct": "D",
    },
    {
        "order": 39,
        "question": (
            "It may be necessary to limit the effectiveness of geo-engineering projects."
        ),
        "correct": "C",
    },
    {
        "order": 40,
        "question": (
            "Research into non-fossil-based fuels cannot be replaced by geo-engineering."
        ),
        "correct": "A",
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
            == "matching_features"
        ]
        for g in existing:
            print(f"Deleting existing MF group {g.id}")
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
            question_type=QuestionType.MATCHING_FEATURES.value,
            instruction=INSTRUCTION,
            subtitle="List of Scientists",
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
                question_type=QuestionType.MATCHING_FEATURES,
                content={"question": item["question"]},
                answer_key={"correct": item["correct"]},
            )
            db.add(q)
            print(f"  Q{item['order']} -> {item['correct']}")

        await db.commit()
        print(
            f"\nDone. Group {group.id} with 4 matching_features questions seeded."
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
