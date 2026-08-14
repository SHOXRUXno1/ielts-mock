"""Seed IELTS 11 Test 2 Listening Part 4 note_completion Q31-40.

Cambridge IELTS 11 Listening Test 2 Section 4 —
Designing a Public Building: The Taylor Concert Hall.
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
from app.services.seed_compound import (
    delete_compound_groups,
    gap_answer_key,
    next_group_order,
)

TEST_ID = uuid.UUID("d82ada15-3d93-40f9-912f-5c1af6d2ce8b")  # Ielts 11 #2
PART4_ID = uuid.UUID("00bfcb9a-eee4-4b76-a1ea-dab2278c9147")

TITLE = "DESIGNING A PUBLIC BUILDING: THE TAYLOR CONCERT HALL"

INSTRUCTION = (
    "Complete the notes below.\n"
    "Write ONE WORD ONLY for each answer."
)

STRUCTURE: dict = {
    "variant": "notes",
    "title": TITLE,
    "bullets": True,
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": (
                "Introduction — The designer of a public building may need "
                "to consider the building's"
            ),
            "items": [
                {"segments": [{"type": "text", "value": "function"}]},
                {
                    "segments": [
                        {"type": "text", "value": "physical and "},
                        {"type": "gap", "gap_id": "g1"},
                        {"type": "text", "value": " context"},
                    ]
                },
                {"segments": [{"type": "text", "value": "symbolic meaning"}]},
            ],
        },
        {
            "heading": "Location and concept of the Concert Hall",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "on the site of a disused "},
                        {"type": "gap", "gap_id": "g2"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "beside a "},
                        {"type": "gap", "gap_id": "g3"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "the design is based on the concept of a mystery",
                        }
                    ]
                },
            ],
        },
        {
            "heading": "Building design",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "it's approached by a "},
                        {"type": "gap", "gap_id": "g4"},
                        {"type": "text", "value": " for pedestrians"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "the building is the shape of a "},
                        {"type": "gap", "gap_id": "g5"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "one exterior wall acts as a large "},
                        {"type": "gap", "gap_id": "g6"},
                    ]
                },
            ],
        },
        {
            "heading": "In the auditorium:",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "the floor is built on huge pads made of ",
                        },
                        {"type": "gap", "gap_id": "g7"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "the walls are made of local wood and are ",
                        },
                        {"type": "gap", "gap_id": "g8"},
                        {"type": "text", "value": " in shape"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "ceiling panels and "},
                        {"type": "gap", "gap_id": "g9"},
                        {
                            "type": "text",
                            "value": " on walls allow adjustment of acoustics",
                        },
                    ]
                },
            ],
        },
        {
            "heading": "Evaluation",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "some critics say the "},
                        {"type": "gap", "gap_id": "g10"},
                        {
                            "type": "text",
                            "value": " style of the building is inappropriate",
                        },
                    ]
                },
            ],
        },
    ],
}

# Cambridge IELTS 11 Listening Test 2 Section 4
ANSWERS: list[tuple[str, list[str]]] = [
    ("g1", ["social"]),
    ("g2", ["factory"]),
    ("g3", ["canal"]),
    ("g4", ["bridge"]),
    ("g5", ["box"]),
    ("g6", ["screen"]),
    ("g7", ["rubber"]),
    ("g8", ["curved"]),
    ("g9", ["curtains"]),
    ("g10", ["international"]),
]


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")

        section = await db.get(Section, PART4_ID)
        if section is None or section.test_id != TEST_ID:
            raise SystemExit(f"Part 4 section {PART4_ID} not found")

        print(f"Test: {test.title} #{getattr(test, 'test_number', '?')}")
        print(f"Section: Listening Part {section.order} ({section.id})")

        removed = await delete_compound_groups(
            db,
            section_id=PART4_ID,
            question_types=("note_completion",),
            order_range=(1, 10),
        )
        if removed:
            print(f"Removed {removed} previous group/orphan row(s)")

        group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PART4_ID,
            order=await next_group_order(db, PART4_ID),
            question_type=QuestionType.NOTE_COMPLETION.value,
            instruction=INSTRUCTION,
            subtitle=None,
            options_shared=STRUCTURE,
        )
        db.add(group)
        await db.flush()

        for i, (gap_id, variants) in enumerate(ANSWERS):
            order = 1 + i
            q = Question(
                id=uuid.uuid4(),
                section_id=PART4_ID,
                question_group_id=group.id,
                order=order,
                question_type=QuestionType.NOTE_COMPLETION,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=1),
            )
            db.add(q)
            print(f"  Q{30 + order} {gap_id} -> {variants}")

        await db.commit()
        print(
            f"\nDone. Group {group.id} with 10 note_completion gaps "
            f"(bullets=true) seeded into IELTS 11-2 Part 4."
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
