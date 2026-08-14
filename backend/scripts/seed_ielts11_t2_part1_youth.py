"""Seed IELTS 11 Test 2 Listening Part 1 note_completion (Youth Council) Q1-10.

Cambridge IELTS 11 Listening Test 2 Section 1 — Enquiry about joining Youth Council.
Renders without bullet markers (bullets: false), matching JumpInto layout.
"""

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
from app.services.seed_compound import (
    delete_compound_groups,
    gap_answer_key,
    next_group_order,
)

TEST_ID = uuid.UUID("d82ada15-3d93-40f9-912f-5c1af6d2ce8b")  # Ielts 11, test_number=2
PART1_ID = uuid.UUID("c125c4f9-b826-4139-9a97-345857004d68")

TITLE = "Enquiry about joining Youth Council"

INSTRUCTION = (
    "Complete the notes below.\n"
    "Write ONE WORD AND/OR A NUMBER for each answer."
)

STRUCTURE: dict = {
    "variant": "notes",
    "title": TITLE,
    "bullets": False,
    "instruction_words": "ONE WORD AND/OR A NUMBER",
    "max_words_per_gap": 3,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "Example  Name: Roger Brown",
                        }
                    ]
                },
                {"segments": [{"type": "text", "value": "Age: 18"}]},
                {
                    "segments": [
                        {"type": "text", "value": "Currently staying in a "},
                        {"type": "gap", "gap_id": "g1"},
                        {"type": "text", "value": " during the week"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Postal address: 17, "},
                        {"type": "gap", "gap_id": "g2"},
                        {"type": "text", "value": " Street, Stamford, Lincs"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Postcode: "},
                        {"type": "gap", "gap_id": "g3"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "Occupation: student and part-time job as a ",
                        },
                        {"type": "gap", "gap_id": "g4"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Studying "},
                        {"type": "gap", "gap_id": "g5"},
                        {
                            "type": "text",
                            "value": " (major subject) and history (minor subject)",
                        },
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Hobbies: does a lot of "},
                        {"type": "gap", "gap_id": "g6"},
                        {"type": "text", "value": ", and is interested in the "},
                        {"type": "gap", "gap_id": "g7"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "On Youth Council, wants to work with young "
                                "people who are "
                            ),
                        },
                        {"type": "gap", "gap_id": "g8"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "Will come to talk to the Elections Officer "
                                "next Monday at "
                            ),
                        },
                        {"type": "gap", "gap_id": "g9"},
                        {"type": "text", "value": " pm"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Mobile number: "},
                        {"type": "gap", "gap_id": "g10"},
                    ]
                },
            ],
        },
    ],
}

# Cambridge IELTS 11 Listening Test 2 Section 1 — JumpInto / official key
ANSWERS: list[tuple[str, list[str], int]] = [
    ("g1", ["hostel"], 1),
    ("g2", ["Buckleigh"], 1),
    ("g3", ["PE97QT", "PE9 7QT", "pe97qt", "pe9 7qt"], 2),
    ("g4", ["waiter"], 1),
    ("g5", ["politics"], 1),
    ("g6", ["cycling"], 1),
    ("g7", ["cinema"], 1),
    ("g8", ["disabled"], 1),
    ("g9", ["4.30", "4:30", "half past four"], 3),
    ("g10", ["07788136711", "07788 136711"], 2),
]


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")

        section = await db.get(
            Section,
            PART1_ID,
            options=[
                selectinload(Section.question_groups).selectinload(
                    QuestionGroup.questions
                )
            ],
        )
        if section is None or section.test_id != TEST_ID:
            raise SystemExit(f"Part 1 section {PART1_ID} not found for this test")

        print(f"Test: {test.title} #{getattr(test, 'test_number', '?')}")
        print(f"Section: Listening Part {section.order} ({section.id})")

        removed = await delete_compound_groups(
            db,
            section_id=PART1_ID,
            question_types=("note_completion", "form_completion"),
            order_range=(1, 10),
        )
        if removed:
            print(f"Removed {removed} previous group/orphan row(s)")

        group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PART1_ID,
            order=await next_group_order(db, PART1_ID),
            question_type=QuestionType.NOTE_COMPLETION.value,
            instruction=INSTRUCTION,
            subtitle=None,
            options_shared=STRUCTURE,
        )
        db.add(group)
        await db.flush()

        for i, (gap_id, variants, max_words) in enumerate(ANSWERS):
            order = 1 + i
            q = Question(
                id=uuid.uuid4(),
                section_id=PART1_ID,
                question_group_id=group.id,
                order=order,
                question_type=QuestionType.NOTE_COMPLETION,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=max_words),
            )
            db.add(q)
            print(f"  Q{order} {gap_id} -> {variants}")

        await db.commit()
        print(
            f"\nDone. Group {group.id} with 10 note_completion gaps "
            f"(bullets=false) seeded into IELTS 11-2 Part 1."
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
