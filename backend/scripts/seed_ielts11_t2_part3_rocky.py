"""Seed IELTS 11 Test 2 Listening Part 3 — Rocky Bay field trip.

Q21-26: MCQ (A/B/C)
Q27-30: two multi_select (choose TWO) questions
"""

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
from app.services.seed_compound import next_group_order

TEST_ID = uuid.UUID("d82ada15-3d93-40f9-912f-5c1af6d2ce8b")  # Ielts 11 #2
PART3_ID = uuid.UUID("35102061-4524-4a13-a48f-bed6c6f4b3d9")

SUBTITLE = "Rocky Bay field trip"
MCQ_INSTRUCTION = "Choose the correct letter, A, B or C."
MULTI_INSTRUCTION = "Choose TWO letters, A-E."

MCQ_ITEMS: list[dict] = [
    {
        "question": "What do the students agree should be included in their aims?",
        "options": [
            "factors affecting where organisms live",
            "the need to preserve endangered species",
            "techniques for classifying different organisms",
        ],
        "correct": "A",
    },
    {
        "question": "What equipment did they forget to take on the Field Trip?",
        "options": ["string", "a compass", "a ruler"],
        "correct": "A",
    },
    {
        "question": "In Helen's procedure section, Colin suggests a change in",
        "options": [
            "the order in which information is given.",
            "the way the information is divided up.",
            "the amount of information provided.",
        ],
        "correct": "C",
    },
    {
        "question": "What do they say about the method they used to measure wave speed?",
        "options": [
            "It provided accurate results.",
            "It was simple to carry out.",
            "It required special equipment.",
        ],
        "correct": "B",
    },
    {
        "question": "What mistake did Helen make when first drawing the map?",
        "options": [
            "She chose the wrong scale.",
            "She stood in the wrong place.",
            "She did it at the wrong time.",
        ],
        "correct": "B",
    },
    {
        "question": "What do they decide to do next with their map?",
        "options": [
            "scan it onto a computer",
            "check it using photographs",
            "add information from the internet",
        ],
        "correct": "B",
    },
]

MULTI_ITEMS: list[dict] = [
    {
        "question": (
            "Which TWO problems affecting organisms in the splash zone "
            "are mentioned?"
        ),
        "options": [
            "lack of water",
            "strong winds",
            "lack of food",
            "high temperatures",
            "large waves",
        ],
        "correct": ["A", "D"],
    },
    {
        "question": (
            "Which TWO reasons for possible error will they include in "
            "their report?"
        ),
        "options": [
            "inaccurate records of the habitat of organisms",
            "influence on behaviour of organisms by observer",
            "incorrect identification of some organisms",
            "making generalisations from a small sample",
            "missing some organisms when counting",
        ],
        "correct": ["C", "E"],
    },
]


async def _wipe_part3(db: AsyncSession) -> int:
    groups = (
        await db.execute(
            select(QuestionGroup).where(QuestionGroup.section_id == PART3_ID)
        )
    ).scalars().all()
    n = 0
    for g in groups:
        qs = (
            await db.execute(
                select(Question).where(Question.question_group_id == g.id)
            )
        ).scalars().all()
        for q in qs:
            await db.delete(q)
        await db.flush()
        await db.delete(g)
        n += 1
    leftovers = (
        await db.execute(select(Question).where(Question.section_id == PART3_ID))
    ).scalars().all()
    for q in leftovers:
        await db.delete(q)
        n += 1
    if n:
        await db.flush()
    return n


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")

        section = await db.get(Section, PART3_ID)
        if section is None or section.test_id != TEST_ID:
            raise SystemExit(f"Part 3 section {PART3_ID} not found")

        print(f"Test: {test.title} #{getattr(test, 'test_number', '?')}")
        print(f"Section: Listening Part {section.order} ({section.id})")

        removed = await _wipe_part3(db)
        if removed:
            print(f"Removed {removed} previous group/question row(s)")

        group_order = await next_group_order(db, PART3_ID)
        order = 1

        mcq_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PART3_ID,
            order=group_order,
            question_type=QuestionType.MCQ.value,
            instruction=MCQ_INSTRUCTION,
            subtitle=SUBTITLE,
            options_shared=None,
        )
        db.add(mcq_group)
        await db.flush()
        group_order += 1

        for item in MCQ_ITEMS:
            q = Question(
                id=uuid.uuid4(),
                section_id=PART3_ID,
                question_group_id=mcq_group.id,
                order=order,
                question_type=QuestionType.MCQ,
                content={
                    "question": item["question"],
                    "options": item["options"],
                },
                answer_key={"correct": item["correct"]},
            )
            db.add(q)
            print(f"  MCQ order={order} -> {item['correct']}")
            order += 1

        for item in MULTI_ITEMS:
            g = QuestionGroup(
                id=uuid.uuid4(),
                section_id=PART3_ID,
                order=group_order,
                question_type=QuestionType.MULTI_SELECT.value,
                instruction=MULTI_INSTRUCTION,
                subtitle=None,
                options_shared=None,
            )
            db.add(g)
            await db.flush()
            group_order += 1

            q = Question(
                id=uuid.uuid4(),
                section_id=PART3_ID,
                question_group_id=g.id,
                order=order,
                question_type=QuestionType.MULTI_SELECT,
                content={
                    "choose_n": 2,
                    "question": item["question"],
                    "options": item["options"],
                },
                answer_key={"correct": item["correct"]},
            )
            db.add(q)
            print(f"  multi_select order={order} -> {item['correct']}")
            order += 1

        await db.commit()
        print(
            "\nDone. Part 3 seeded: 6 MCQ + 2 multi_select "
            "(10 scoring slots). Rocky Bay field trip."
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
