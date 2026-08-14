"""Seed Listening Part 4 note_completion (Q31-40) Ocean Biodiversity into IELTS 11."""

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

INSTRUCTION = "Complete the notes below. Write ONE WORD ONLY for each answer."

STRUCTURE: dict = {
    "variant": "notes",
    "title": "Ocean Biodiversity",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "Biodiversity hotspots",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "areas containing many different species"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "important for locating targets for "},
                        {"type": "gap", "gap_id": "g1"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "at first only identified on land"},
                    ]
                },
            ],
        },
        {
            "heading": "Boris Worm, 2005",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "identified hotspots for large ocean predators, e.g. sharks",
                        }
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "found that ocean hotspots:"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "were not always rich in "},
                        {"type": "gap", "gap_id": "g2"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "had higher temperatures at the "},
                        {"type": "gap", "gap_id": "g3"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "had sufficient "},
                        {"type": "gap", "gap_id": "g4"},
                        {"type": "text", "value": " in the water"},
                    ]
                },
            ],
        },
        {
            "heading": "Lisa Ballance, 2007",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "looked for hotspots for marine "},
                        {"type": "gap", "gap_id": "g5"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "found these were all located where ocean currents meet",
                        }
                    ]
                },
            ],
        },
        {
            "heading": "Census of Marine Life",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "found new ocean species living:"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "under the "},
                        {"type": "gap", "gap_id": "g6"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "near volcanoes on the ocean floor",
                        }
                    ]
                },
            ],
        },
        {
            "heading": "Global Marine Species Assessment",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "want to list endangered ocean species, considering:",
                        }
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "population size"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "geographical distribution"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "rate of "},
                        {"type": "gap", "gap_id": "g7"},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "Aim: to assess 20,000 species and make a distribution ",
                        },
                        {"type": "gap", "gap_id": "g8"},
                        {"type": "text", "value": " for each one"},
                    ]
                },
            ],
        },
        {
            "heading": "Recommendations to retain ocean biodiversity",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "increase the number of ocean reserves"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "establish "},
                        {"type": "gap", "gap_id": "g9"},
                        {"type": "text", "value": " corridors (e.g. for turtles)"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "reduce fishing quotas"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "catch fish only for the purpose of "},
                        {"type": "gap", "gap_id": "g10"},
                    ]
                },
            ],
        },
    ],
}

# Cambridge IELTS 11 Listening Test 1 Part 4 answer key
ANSWERS: list[tuple[str, list[str]]] = [
    ("g1", ["conservation"]),
    ("g2", ["food", "foods"]),
    ("g3", ["surface"]),
    ("g4", ["oxygen", "O2", "o2"]),
    ("g5", ["mammals"]),
    ("g6", ["ice"]),
    ("g7", ["decline", "declining", "decrease"]),
    ("g8", ["map"]),
    ("g9", ["migration"]),
    ("g10", ["consumption"]),
]


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")

        result = await db.execute(
            select(Section)
            .options(
                selectinload(Section.question_groups).selectinload(QuestionGroup.questions)
            )
            .where(Section.test_id == TEST_ID, Section.type == "listening")
            .order_by(Section.order)
        )
        listening = list(result.scalars().all())
        print(f"Found {len(listening)} listening section(s) for {test.title}")
        if len(listening) < 4:
            raise SystemExit(f"Need 4 listening parts; found {len(listening)}")

        part4 = sorted(listening, key=lambda s: s.order)[3]
        print(f"Using Part 4 section id={part4.id} order={part4.order}")

        # Idempotent: remove previous Ocean Biodiversity note groups
        existing = [
            g
            for g in (part4.question_groups or [])
            if str(getattr(g.question_type, "value", g.question_type)) == "note_completion"
            and isinstance(g.options_shared, dict)
            and g.options_shared.get("title") == "Ocean Biodiversity"
        ]
        for g in existing:
            print(f"Deleting existing group {g.id}")
            await db.delete(g)
        if existing:
            await db.flush()

        remaining = await db.execute(
            select(QuestionGroup).where(QuestionGroup.section_id == part4.id)
        )
        max_group_order = max((g.order for g in remaining.scalars().all()), default=0)

        group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=part4.id,
            order=max_group_order + 1,
            question_type=QuestionType.NOTE_COMPLETION.value,
            instruction=INSTRUCTION,
            subtitle=None,
            options_shared=STRUCTURE,
        )
        db.add(group)
        await db.flush()

        q_result = await db.execute(
            select(Question).where(Question.section_id == part4.id)
        )
        next_order = max((q.order for q in q_result.scalars().all()), default=0) + 1

        for i, (gap_id, variants) in enumerate(ANSWERS, start=1):
            q = Question(
                id=uuid.uuid4(),
                section_id=part4.id,
                question_group_id=group.id,
                order=next_order,
                question_type=QuestionType.NOTE_COMPLETION,
                content={"gap_id": gap_id},
                answer_key={
                    "correct": variants,
                    "max_words": 1,
                    "case_sensitive": False,
                },
            )
            db.add(q)
            print(f"  Q{30 + i} {gap_id} order={next_order} -> {variants}")
            next_order += 1

        await db.commit()
        print(f"\nDone. Group {group.id} with 10 note_completion gaps seeded into Part 4.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
