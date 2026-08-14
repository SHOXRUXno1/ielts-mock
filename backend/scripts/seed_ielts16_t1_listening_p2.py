"""Seed IELTS 16 Test 1 Listening Part 2 — Stevenson's site.

Q11-14: MCQ (A/B/C)
Q15-20: map_labeling (Plan of Stevenson's site — upload image in admin)

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_ielts16_t1_listening_p2.py
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

TEST_ID = uuid.UUID("4cdab44f-db90-4122-a02b-d7df41fc400a")  # Ielts 16
PART2_ID = uuid.UUID("9fea45dd-cbef-4d07-ae25-0787d97a80fe")

MCQ_INSTRUCTION = "Choose the correct letter, A, B or C."

MCQ_ITEMS: list[dict] = [
    {
        "question": "Stevenson's was founded in",
        "options": [
            "1923.",
            "1924.",
            "1926.",
        ],
        "correct": "C",
    },
    {
        "question": "Originally, Stevenson's manufactured goods for",
        "options": [
            "the healthcare industry.",
            "the automotive industry.",
            "the machine tools industry.",
        ],
        "correct": "A",
    },
    {
        "question": "What does the speaker say about the company premises?",
        "options": [
            "The company has recently moved.",
            "The company has no plans to move.",
            "The company is going to move shortly.",
        ],
        "correct": "B",
    },
    {
        "question": "The programme for the work experience group includes",
        "options": [
            "time to do research.",
            "meetings with a teacher.",
            "talks by staff.",
        ],
        "correct": "C",
    },
]

MAP_INSTRUCTION = (
    "Label the map below.\n"
    "Choose the correct letter, A-J, next to Questions 15-20."
)

MAP_OPTIONS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

# Cambridge IELTS 16 Listening Test 1 Section 2 map answers
MAP_ITEMS: list[tuple[str, str]] = [
    ("coffee room", "H"),
    ("warehouse", "C"),
    ("staff canteen", "G"),
    ("meeting room", "B"),
    ("human resources", "I"),
    ("boardroom", "A"),
]


async def _wipe_part2(db: AsyncSession) -> int:
    groups = (
        await db.execute(
            select(QuestionGroup).where(QuestionGroup.section_id == PART2_ID)
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
        await db.execute(select(Question).where(Question.section_id == PART2_ID))
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

        section = await db.get(Section, PART2_ID)
        if section is None or section.test_id != TEST_ID:
            raise SystemExit(f"Part 2 section {PART2_ID} not found")

        section.title = "Part 2 — Stevenson's"
        print(f"Test: {test.title} #{getattr(test, 'test_number', '?')}")
        print(f"Section: Listening Part {section.order} ({section.id})")

        removed = await _wipe_part2(db)
        if removed:
            print(f"Removed {removed} previous group/question row(s)")

        # Section-local order (1..N). Display numbers 11-20 come from Part 1 offset.
        order = 1
        group_order = await next_group_order(db, PART2_ID)

        mcq_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PART2_ID,
            order=group_order,
            question_type=QuestionType.MCQ.value,
            instruction=MCQ_INSTRUCTION,
            subtitle=None,
            options_shared=None,
        )
        db.add(mcq_group)
        await db.flush()
        group_order += 1

        for item in MCQ_ITEMS:
            q = Question(
                id=uuid.uuid4(),
                section_id=PART2_ID,
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
            print(f"  mcq order={order} -> {item['correct']} (display ~Q{10 + order})")
            order += 1

        map_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PART2_ID,
            order=group_order,
            question_type=QuestionType.MAP_LABELING.value,
            instruction=MAP_INSTRUCTION,
            subtitle="Plan of Stevenson's site",
            options_shared={"options": MAP_OPTIONS, "image_url": None},
        )
        db.add(map_group)
        await db.flush()

        for location, letter in MAP_ITEMS:
            q = Question(
                id=uuid.uuid4(),
                section_id=PART2_ID,
                question_group_id=map_group.id,
                order=order,
                question_type=QuestionType.MAP_LABELING,
                content={"location": location},
                answer_key={"correct": letter},
            )
            db.add(q)
            print(f"  map order={order} {location!r} -> {letter} (display ~Q{10 + order})")
            order += 1

        await db.commit()
        print(
            "\nDone. Part 2 seeded: 4 MCQ + 6 map_labeling.\n"
            "Upload the Stevenson's site plan image in admin "
            "(question group options_shared.image_url).\n"
            "Note: display numbers are 11-20 only after Part 1 has 10 scoring slots."
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
