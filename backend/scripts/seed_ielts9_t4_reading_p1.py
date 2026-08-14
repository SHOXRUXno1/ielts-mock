"""
Seed IELTS Reading Passage 1 for Cambridge IELTS 9 – Test 4
(content from Cambridge 19 Test 4 Passage 1 — butterflies).

Groups:
  1. true_false_ng Q1-6
  2. note_completion Q7-13 ("Butterflies in the UK")

Usage:
    cd backend
    venv\\Scripts\\python scripts\\seed_ielts9_t4_reading_p1.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, selectinload

from app.core.config import settings
from app.models.question import Question
from app.models.question_group import QuestionGroup
from app.models.section import Section, SectionType
from app.models.test import Test
from app.services.seed_compound import gap_answer_key

TEST_TITLE = "Cambridge IELTS 9 \u2013 Test 4"
PASSAGE_TITLE = "The impact of climate change on butterflies in Britain"

TFNG_INSTRUCTION = (
    "Do the following statements agree with the information given in Reading Passage 1?\n"
    "In boxes 1\u20136 on your answer sheet, choose"
)

TFNG_QUESTIONS = [
    {
        "order": 1,
        "statement": "Forty years ago, there were fewer butterflies in Britain than at present.",
        "correct": "False",
    },
    {
        "order": 2,
        "statement": "Caterpillars are eaten by a number of different predators.",
        "correct": "True",
    },
    {
        "order": 3,
        "statement": (
            "\u2018Phenology\u2019 is a term used to describe a creature\u2019s ability "
            "to alter the location of a lifecycle event."
        ),
        "correct": "False",
    },
    {
        "order": 4,
        "statement": (
            "Some species of butterfly have a reduced lifespan due to spring "
            "temperature increases."
        ),
        "correct": "Not Given",
    },
    {
        "order": 5,
        "statement": (
            "There is a clear reason for the adaptations that butterflies are "
            "making to climate change."
        ),
        "correct": "False",
    },
    {
        "order": 6,
        "statement": (
            "The data used in the study was taken from the work of amateur "
            "butterfly watchers."
        ),
        "correct": "True",
    },
]

NOTES_INSTRUCTION = (
    "Complete the notes below.\n"
    "Choose ONE WORD ONLY from the passage for each answer.\n"
    "Write your answers in boxes 7\u201313 on your answer sheet."
)

NOTES_STRUCTURE = {
    "variant": "notes",
    "title": "Butterflies in the UK",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "The Small Blue",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "lives in large "},
                        {"type": "gap", "gap_id": "g1"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "first appears at the start of "},
                        {"type": "gap", "gap_id": "g2"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "completes more than one reproductive cycle per year",
                        }
                    ]
                },
            ],
        },
        {
            "heading": "The High Brown Fritillary",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "has one reproductive cycle"}
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "is considered to be more "},
                        {"type": "gap", "gap_id": "g3"},
                        {"type": "text", "value": " than other species"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "its caterpillars occupy a limited range of ",
                        },
                        {"type": "gap", "gap_id": "g4"},
                    ]
                },
            ],
        },
        {
            "heading": "The Silver-studded Blue",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "is already able to reproduce twice a year in warm areas of ",
                        },
                        {"type": "gap", "gap_id": "g5"},
                    ]
                },
            ],
        },
        {
            "heading": "The White Admiral",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "is found in "},
                        {"type": "gap", "gap_id": "g6"},
                        {"type": "text", "value": " areas of England"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "both climate change and the ",
                        },
                        {"type": "gap", "gap_id": "g7"},
                        {
                            "type": "text",
                            "value": " of the caterpillar are possible reasons for decline",
                        },
                    ]
                },
            ],
        },
    ],
}

NOTES_ANSWERS = [
    ("g1", 7, ["colonies", "colony"]),
    ("g2", 8, ["spring"]),
    ("g3", 9, ["endangered"]),
    ("g4", 10, ["habitats", "habitat"]),
    ("g5", 11, ["Europe"]),
    ("g6", 12, ["southern"]),
    ("g7", 13, ["diet"]),
]


async def main() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        test = (
            await session.execute(select(Test).where(Test.title == TEST_TITLE))
        ).scalar_one_or_none()
        if test is None:
            print(f"ERROR: Test '{TEST_TITLE}' not found.")
            return

        print(f"Found test: {test.title} (id={test.id})")

        # Drop empty placeholder reading sections (order 10/11 with no passage)
        empty = await session.execute(
            select(Section).where(
                Section.test_id == test.id,
                Section.type == SectionType.READING,
                Section.order.in_([10, 11]),
            )
        )
        for old in empty.scalars().all():
            if not (old.passage or "").strip():
                print(f"  Deleting empty reading section order={old.order}")
                await session.delete(old)
        await session.flush()

        # Find butterfly passage section
        result = await session.execute(
            select(Section)
            .options(
                selectinload(Section.question_groups).selectinload(
                    QuestionGroup.questions
                )
            )
            .where(
                Section.test_id == test.id,
                Section.type == SectionType.READING,
            )
            .order_by(Section.order)
        )
        sections = list(result.scalars().all())
        section = next(
            (s for s in sections if (s.title or "") == PASSAGE_TITLE),
            None,
        )
        if section is None:
            section = next((s for s in sections if (s.passage or "").strip()), None)

        if section is None:
            print("ERROR: No reading passage section found.")
            return

        # Normalise to Passage 1 order
        section.order = 10
        section.title = PASSAGE_TITLE
        await session.flush()
        print(f"  Using section order={section.order} id={section.id}")

        # Clear existing groups for re-seed
        for g in list(section.question_groups or []):
            await session.delete(g)
        await session.flush()

        # ── Group 1: TFNG Q1-6 ────────────────────────────────────────────
        group_tfng = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=1,
            question_type="true_false_ng",
            instruction=TFNG_INSTRUCTION,
        )
        session.add(group_tfng)
        await session.flush()

        for item in TFNG_QUESTIONS:
            session.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=section.id,
                    question_group_id=group_tfng.id,
                    order=item["order"],
                    question_type="true_false_ng",
                    content={"statement": item["statement"]},
                    answer_key={"correct": item["correct"]},
                )
            )
        print(f"    Added {len(TFNG_QUESTIONS)} TFNG questions (Q1-6)")

        # ── Group 2: Notes Q7-13 ──────────────────────────────────────────
        group_notes = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=2,
            question_type="note_completion",
            instruction=NOTES_INSTRUCTION,
            options_shared=NOTES_STRUCTURE,
        )
        session.add(group_notes)
        await session.flush()

        for gap_id, order, variants in NOTES_ANSWERS:
            session.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=section.id,
                    question_group_id=group_notes.id,
                    order=order,
                    question_type="note_completion",
                    content={"gap_id": gap_id},
                    answer_key=gap_answer_key(variants, max_words=1),
                )
            )
        print(f"    Added {len(NOTES_ANSWERS)} note_completion questions (Q7-13)")

        await session.commit()
        print("\nDone! Reading Passage 1 seeded successfully.")


if __name__ == "__main__":
    asyncio.run(main())
