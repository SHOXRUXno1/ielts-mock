"""Seed IELTS 16 Test 1 Listening Part 1 — Children's Engineering Workshops.

Q1-10: note_completion (ONE WORD AND/OR A NUMBER)

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_ielts16_t1_listening_p1.py
"""

from __future__ import annotations

import asyncio
import uuid

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

TEST_ID = uuid.UUID("4cdab44f-db90-4122-a02b-d7df41fc400a")  # Ielts 16
PART1_ID = uuid.UUID("6ee7750b-e25a-455b-915f-97c24829d179")

INSTRUCTION = (
    "Complete the notes below.\n"
    "Write ONE WORD AND/OR A NUMBER for each answer."
)

STRUCTURE: dict = {
    "variant": "notes",
    "title": "Children's Engineering Workshops",
    "instruction_words": "ONE WORD AND/OR A NUMBER",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "Tiny Engineers (ages 4–5)",
            "items": [
                {"segments": [{"type": "text", "value": "Activities"}]},
                {
                    "segments": [
                        {"type": "text", "value": "Create a cover for an "},
                        {"type": "gap", "gap_id": "g1"},
                        {
                            "type": "text",
                            "value": (
                                " so they can drop it from a height "
                                "without breaking it."
                            ),
                        },
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "Take part in a competition to build "
                                "the tallest "
                            ),
                        },
                        {"type": "gap", "gap_id": "g2"},
                        {"type": "text", "value": "."},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Make a "},
                        {"type": "gap", "gap_id": "g3"},
                        {"type": "text", "value": " powered by a balloon."},
                    ]
                },
            ],
        },
        {
            "heading": "Junior Engineers (ages 6–8)",
            "items": [
                {"segments": [{"type": "text", "value": "Activities"}]},
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "Build model cars, trucks and ",
                        },
                        {"type": "gap", "gap_id": "g4"},
                        {
                            "type": "text",
                            "value": (
                                " and learn how to program them so "
                                "they can move."
                            ),
                        },
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "Take part in a competition to build "
                                "the longest "
                            ),
                        },
                        {"type": "gap", "gap_id": "g5"},
                        {
                            "type": "text",
                            "value": " using card and wood.",
                        },
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Create a short "},
                        {"type": "gap", "gap_id": "g6"},
                        {
                            "type": "text",
                            "value": " with special software.",
                        },
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Build, "},
                        {"type": "gap", "gap_id": "g7"},
                        {
                            "type": "text",
                            "value": " and program a humanoid robot.",
                        },
                    ]
                },
                {"segments": [{"type": "text", "value": "Other details:"}]},
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "Cost for a five-week block: £50",
                        }
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Held on "},
                        {"type": "gap", "gap_id": "g8"},
                        {
                            "type": "text",
                            "value": " from 10 am to 11 am",
                        },
                    ]
                },
            ],
        },
        {
            "heading": "Location",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "Building 10A, "},
                        {"type": "gap", "gap_id": "g9"},
                        {
                            "type": "text",
                            "value": " Industrial Estate, Grasford",
                        },
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Plenty of "},
                        {"type": "gap", "gap_id": "g10"},
                        {"type": "text", "value": " is available."},
                    ]
                },
            ],
        },
    ],
}

# Cambridge IELTS 16 Listening Test 1 Section 1 answers
ANSWERS: list[tuple[str, list[str]]] = [
    ("g1", ["egg"]),
    ("g2", ["tower"]),
    ("g3", ["car"]),
    ("g4", ["animals"]),
    ("g5", ["bridge"]),
    ("g6", ["movie", "film"]),
    ("g7", ["decorate"]),
    ("g8", ["Wednesdays", "Wednesday"]),
    ("g9", ["Fradstone"]),
    ("g10", ["parking"]),
]


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")

        section = await db.get(Section, PART1_ID)
        if section is None or section.test_id != TEST_ID:
            raise SystemExit(f"Part 1 section {PART1_ID} not found")

        section.title = "Part 1 — Children's Engineering Workshops"
        print(f"Test: {test.title} #{getattr(test, 'test_number', '?')}")
        print(f"Section: Listening Part {section.order} ({section.id})")
        if section.audio_url:
            print(f"Keeping audio_url: {section.audio_url}")

        removed = await delete_compound_groups(
            db,
            section_id=PART1_ID,
            question_types=("note_completion",),
            title="Children's Engineering Workshops",
        )
        if removed:
            print(f"Removed {removed} previous group/question row(s)")

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

        for i, (gap_id, variants) in enumerate(ANSWERS, start=1):
            q = Question(
                id=uuid.uuid4(),
                section_id=PART1_ID,
                question_group_id=group.id,
                order=i,
                question_type=QuestionType.NOTE_COMPLETION,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=1),
            )
            db.add(q)
            print(f"  Q{i} {gap_id} -> {variants}")

        await db.commit()
        print(
            f"\nDone. Group {group.id} with 10 note_completion gaps "
            "seeded into Part 1."
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
