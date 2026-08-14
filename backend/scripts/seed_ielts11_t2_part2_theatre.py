"""Seed IELTS 11 Test 2 Listening Part 2 — New staff at theatre.

Q11-16: three multi_select (choose TWO) questions
Q17-20: map_labeling (ground floor plan — upload image in admin)
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
PART2_ID = uuid.UUID("925f53fb-5b56-49fd-b71c-534498d20533")

MULTI_SELECT_INSTRUCTION = "Choose TWO letters, A-E."

# Each item → one QuestionGroup with one multi_select question (choose_n=2 → 2 slots)
MULTI_ITEMS: list[dict] = [
    {
        "question": (
            "Which TWO changes have been made so far during the "
            "refurbishment of the theatre?"
        ),
        "options": [
            "Some rooms now have a different use.",
            "A different type of seating has been installed.",
            "An elevator has been installed.",
            "The outside of the building has been repaired.",
            "Extra seats have been added.",
        ],
        "correct": ["A", "B"],
    },
    {
        "question": (
            "Which TWO facilities does the theatre currently offer to the public?"
        ),
        "options": [
            "rooms for hire",
            "backstage tours",
            "hire of costumes",
            "a bookshop",
            "a café",
        ],
        "correct": ["B", "D"],
    },
    {
        "question": "Which TWO workshops does the theatre currently offer?",
        "options": [
            "sound",
            "acting",
            "making puppets",
            "make-up",
            "lighting",
        ],
        "correct": ["C", "E"],
    },
]

MAP_INSTRUCTION = (
    "Label the plan below.\n"
    "Choose the correct letter, A-G, next to Questions 17-20."
)

MAP_OPTIONS = ["A", "B", "C", "D", "E", "F", "G"]

# Cambridge IELTS 11 Listening Test 2 Section 2 map answers
MAP_ITEMS: list[tuple[str, str]] = [
    ("box office", "G"),
    ("theatre manager's office", "D"),
    ("lighting box", "B"),
    ("artistic director's office", "F"),
]


async def _wipe_part2(db: AsyncSession) -> int:
    """Delete existing groups + questions on Part 2 (questions first)."""
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

        print(f"Test: {test.title} #{getattr(test, 'test_number', '?')}")
        print(f"Section: Listening Part {section.order} ({section.id})")

        removed = await _wipe_part2(db)
        if removed:
            print(f"Removed {removed} previous group/question row(s)")

        order = 1
        group_order = await next_group_order(db, PART2_ID)

        for item in MULTI_ITEMS:
            group = QuestionGroup(
                id=uuid.uuid4(),
                section_id=PART2_ID,
                order=group_order,
                question_type=QuestionType.MULTI_SELECT.value,
                instruction=MULTI_SELECT_INSTRUCTION,
                subtitle=None,
                options_shared=None,
            )
            db.add(group)
            await db.flush()

            q = Question(
                id=uuid.uuid4(),
                section_id=PART2_ID,
                question_group_id=group.id,
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
            print(
                f"  multi_select order={order} correct={item['correct']} "
                f"slots ~{10 + order * 2 - 1}-{10 + order * 2}"
            )
            order += 1
            group_order += 1

        map_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PART2_ID,
            order=group_order,
            question_type=QuestionType.MAP_LABELING.value,
            instruction=MAP_INSTRUCTION,
            subtitle=None,
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
            print(f"  map order={order} {location!r} -> {letter}")
            order += 1

        await db.commit()
        print(
            f"\nDone. Part 2 seeded: 3 multi_select (6 slots) + "
            f"4 map_labeling. Upload the theatre plan image in admin."
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
