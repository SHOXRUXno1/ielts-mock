"""Seed Reading Passage 2 diagram_labeling Q20-26 (Falkirk Wheel diagram) into IELTS 11."""

from __future__ import annotations

import asyncio
import uuid

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

TEST_ID = uuid.UUID("1f4988f6-52d0-49d7-881e-3be2032f9429")
PASSAGE2_ID = uuid.UUID("94877ee7-e06b-4f82-b799-b73d77884fae")

TITLE = "How a boat is lifted on the Falkirk Wheel"

INSTRUCTION = (
    "Label the diagram below.\n"
    "Choose ONE WORD from the passage for each answer.\n"
    "Write your answers in boxes 20-26 on your answer sheet."
)

STRUCTURE: dict = {
    "variant": "notes",
    "title": TITLE,
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    # image_url left empty — upload diagram scan in admin wizard
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "A pair of ",
                        },
                        {"type": "gap", "gap_id": "g1"},
                        {
                            "type": "text",
                            "value": " are lifted in order to shut out water from canal basin",
                        },
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "A "},
                        {"type": "gap", "gap_id": "g2"},
                        {
                            "type": "text",
                            "value": " is taken out, enabling Wheel to rotate",
                        },
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Hydraulic motors drive "},
                        {"type": "gap", "gap_id": "g3"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "A range of different-sized ",
                        },
                        {"type": "gap", "gap_id": "g4"},
                        {
                            "type": "text",
                            "value": " ensures boat keeps upright",
                        },
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "Boat reaches top Wheel, then moves directly onto ",
                        },
                        {"type": "gap", "gap_id": "g5"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "Boat travels through tunnel beneath Roman ",
                        },
                        {"type": "gap", "gap_id": "g6"},
                    ]
                },
                {
                    "segments": [
                        {"type": "gap", "gap_id": "g7"},
                        {
                            "type": "text",
                            "value": " raise boat 11 m to level of Union Canal",
                        },
                    ]
                },
            ],
        },
    ],
}

# Cambridge IELTS 11 Reading Test 1 Passage 2 diagram answers
ANSWERS: list[tuple[str, list[str]]] = [
    ("g1", ["gates"]),
    ("g2", ["clamp"]),
    ("g3", ["axle"]),
    ("g4", ["cogs"]),
    ("g5", ["aqueduct"]),
    ("g6", ["wall"]),
    ("g7", ["locks"]),
]


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")

        section = await db.get(
            Section,
            PASSAGE2_ID,
            options=[
                selectinload(Section.question_groups).selectinload(
                    QuestionGroup.questions
                )
            ],
        )
        if section is None:
            raise SystemExit(f"Section {PASSAGE2_ID} not found")

        print(f"Test: {test.title}")
        print(f"Passage: {section.title} ({section.id})")

        # Wipe every note/diagram group on this passage (not only matching title)
        # so a prior seed cannot leave ghost gaps beside the new group.
        removed = await delete_compound_groups(
            db,
            section_id=PASSAGE2_ID,
            question_types=("note_completion", "diagram_labeling"),
            order_range=(20, 26),
        )
        if removed:
            print(f"Removed {removed} previous diagram/note group row(s)")

        group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PASSAGE2_ID,
            order=await next_group_order(db, PASSAGE2_ID),
            question_type=QuestionType.DIAGRAM_LABELING.value,
            instruction=INSTRUCTION,
            subtitle=None,
            options_shared=STRUCTURE,
        )
        db.add(group)
        await db.flush()

        for i, (gap_id, variants) in enumerate(ANSWERS):
            order = 20 + i
            q = Question(
                id=uuid.uuid4(),
                section_id=PASSAGE2_ID,
                question_group_id=group.id,
                order=order,
                question_type=QuestionType.DIAGRAM_LABELING,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=1),
            )
            db.add(q)
            print(f"  Q{order} {gap_id} -> {variants}")

        await db.commit()
        print(
            f"\nDone. Group {group.id} with 7 diagram_labeling gaps seeded into Passage 2."
        )
        print("Upload the Falkirk Wheel diagram image in the admin wizard.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
