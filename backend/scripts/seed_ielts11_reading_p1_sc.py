"""Seed Reading Passage 1 sentence_completion Q1-7 (Indoor farming) into IELTS 11."""

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
GROUP_ID = uuid.UUID("e28a8959-9c3a-4918-81e3-3b89b88fdecd")

INSTRUCTION = (
    "Complete the sentences below.\n"
    "Choose NO MORE THAN TWO WORDS from the passage for each answer.\n"
    "Write your answers in boxes 1-7 on your answer sheet."
)

# Cambridge IELTS 11 Reading Test 1 Passage 1 — Indoor farming
QUESTIONS: list[dict] = [
    {
        "order": 1,
        "prompt": "Some food plants, including ____, are already grown indoors.",
        "correct": ["tomatoes"],
    },
    {
        "order": 2,
        "prompt": (
            "Vertical farms would be located in ____, meaning that there would "
            "be less need to take them long distances to customers."
        ),
        "correct": ["urban centres", "urban centers"],
    },
    {
        "order": 3,
        "prompt": (
            "Vertical farms could use methane from plants and animals to produce ____."
        ),
        "correct": ["energy"],
    },
    {
        "order": 4,
        "prompt": (
            "The consumption of ____ would be cut because agricultural vehicles "
            "would be unnecessary."
        ),
        "correct": ["fossil fuel", "fossil fuels"],
    },
    {
        "order": 5,
        "prompt": (
            "The fact that vertical farms would need ____ light is a disadvantage."
        ),
        "correct": ["artificial"],
    },
    {
        "order": 6,
        "prompt": (
            "One form of vertical farming involves planting in ____ which are not fixed."
        ),
        "correct": ["trays"],
    },
    {
        "order": 7,
        "prompt": (
            "The most probable development is that food will be grown on ____ "
            "in towns and cities."
        ),
        "correct": ["rooftops"],
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

        section = await db.get(Section, PASSAGE1_ID)
        if section is None:
            raise SystemExit(f"Section {PASSAGE1_ID} not found")

        print(f"Test: {test.title}")
        print(f"Passage: {section.title} ({section.id})")
        print(f"Group: {group.subtitle} ({group.id})")

        # Clear existing questions in this group (idempotent)
        existing = await db.execute(
            select(Question).where(Question.question_group_id == GROUP_ID)
        )
        for q in existing.scalars().all():
            print(f"Deleting existing question order={q.order}")
            await db.delete(q)
        await db.flush()

        group.instruction = INSTRUCTION
        group.subtitle = "Indoor farming"
        group.question_type = QuestionType.SENTENCE_COMPLETION.value

        for item in QUESTIONS:
            q = Question(
                id=uuid.uuid4(),
                section_id=PASSAGE1_ID,
                question_group_id=GROUP_ID,
                order=item["order"],
                question_type=QuestionType.SENTENCE_COMPLETION,
                content={
                    "prompt": item["prompt"],
                    "max_words": 2,
                },
                answer_key={
                    "correct": item["correct"],
                    "case_sensitive": False,
                    "max_words": 2,
                },
            )
            db.add(q)
            print(f"  Q{item['order']} -> {item['correct']}")

        await db.commit()
        print("\nDone. 7 sentence_completion questions seeded into Passage 1.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
