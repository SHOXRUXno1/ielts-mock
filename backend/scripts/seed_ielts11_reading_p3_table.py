"""Seed Reading Passage 3 table_completion Q30-36 into IELTS 11."""

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
PASSAGE3_ID = uuid.UUID("9c78a0d6-ada1-434b-b1cb-7398e6fe4ad8")

INSTRUCTION = (
    "Complete the table below.\n"
    "Choose ONE WORD from the passage for each answer.\n"
    "Write your answers in boxes 30-36 on your answer sheet."
)

SUBTITLE = "GEO-ENGINEERING PROJECTS"

STRUCTURE: dict = {
    "variant": "table",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "headers": ["Procedure", "Aim"],
    "rows": [
        [
            {
                "variant": "plain",
                "segments": [
                    {
                        "type": "text",
                        "value": (
                            "put a large number of tiny spacecraft into "
                            "orbit far above Earth"
                        ),
                    }
                ],
            },
            {
                "variant": "plain",
                "segments": [
                    {"type": "text", "value": "to create a "},
                    {"type": "gap", "gap_id": "g1"},
                    {
                        "type": "text",
                        "value": " that would reduce the amount of light reaching Earth",
                    },
                ],
            },
        ],
        [
            {
                "variant": "plain",
                "segments": [
                    {"type": "text", "value": "place "},
                    {"type": "gap", "gap_id": "g2"},
                    {"type": "text", "value": " in the sea"},
                ],
            },
            {
                "variant": "plain",
                "segments": [
                    {"type": "text", "value": "to encourage "},
                    {"type": "gap", "gap_id": "g3"},
                    {"type": "text", "value": " to form"},
                ],
            },
        ],
        [
            {
                "variant": "plain",
                "segments": [
                    {
                        "type": "text",
                        "value": "release aerosol sprays into the stratosphere",
                    }
                ],
            },
            {
                "variant": "plain",
                "segments": [
                    {"type": "text", "value": "to create "},
                    {"type": "gap", "gap_id": "g4"},
                    {
                        "type": "text",
                        "value": " that would reduce the amount of light reaching Earth",
                    },
                ],
            },
        ],
        [
            {
                "variant": "plain",
                "segments": [
                    {"type": "text", "value": "fix strong "},
                    {"type": "gap", "gap_id": "g5"},
                    {"type": "text", "value": " to Greenland ice sheets"},
                ],
            },
            {
                "variant": "plain",
                "segments": [
                    {
                        "type": "text",
                        "value": "to prevent icebergs moving into the sea",
                    }
                ],
            },
        ],
        [
            {
                "variant": "plain",
                "segments": [
                    {
                        "type": "text",
                        "value": (
                            "plant trees in Russian Arctic that would "
                            "lose their leaves in winter"
                        ),
                    }
                ],
            },
            {
                "variant": "plain",
                "segments": [
                    {"type": "text", "value": "to allow the "},
                    {"type": "gap", "gap_id": "g6"},
                    {"type": "text", "value": " to reflect radiation"},
                ],
            },
        ],
        [
            {
                "variant": "plain",
                "segments": [
                    {"type": "text", "value": "change the direction of "},
                    {"type": "gap", "gap_id": "g7"},
                ],
            },
            {
                "variant": "plain",
                "segments": [
                    {
                        "type": "text",
                        "value": "to bring more cold water into ice-forming areas",
                    }
                ],
            },
        ],
    ],
}

# Cambridge IELTS 11 Reading Test 1 Passage 3 — table answers
ANSWERS: list[tuple[str, list[str]]] = [
    ("g1", ["sunshade"]),
    ("g2", ["iron"]),
    ("g3", ["algae"]),
    ("g4", ["clouds"]),
    ("g5", ["cables"]),
    ("g6", ["snow"]),
    ("g7", ["rivers"]),
]


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")

        section = await db.get(
            Section,
            PASSAGE3_ID,
            options=[
                selectinload(Section.question_groups).selectinload(
                    QuestionGroup.questions
                )
            ],
        )
        if section is None:
            raise SystemExit(f"Section {PASSAGE3_ID} not found")

        print(f"Test: {test.title}")
        print(f"Passage: {section.title} ({section.id})")

        existing = [
            g
            for g in (section.question_groups or [])
            if str(getattr(g.question_type, "value", g.question_type))
            == "table_completion"
            and isinstance(g.options_shared, dict)
            and (g.subtitle or "") == SUBTITLE
        ]
        for g in existing:
            print(f"Deleting existing group {g.id}")
            await db.delete(g)
        if existing:
            await db.flush()

        remaining = await db.execute(
            select(QuestionGroup).where(QuestionGroup.section_id == PASSAGE3_ID)
        )
        max_group_order = max((g.order for g in remaining.scalars().all()), default=0)

        group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PASSAGE3_ID,
            order=max_group_order + 1,
            question_type=QuestionType.TABLE_COMPLETION.value,
            instruction=INSTRUCTION,
            subtitle=SUBTITLE,
            options_shared=STRUCTURE,
        )
        db.add(group)
        await db.flush()

        for i, (gap_id, variants) in enumerate(ANSWERS):
            order = 30 + i
            q = Question(
                id=uuid.uuid4(),
                section_id=PASSAGE3_ID,
                question_group_id=group.id,
                order=order,
                question_type=QuestionType.TABLE_COMPLETION,
                content={"gap_id": gap_id},
                answer_key={
                    "correct": variants,
                    "max_words": 1,
                    "case_sensitive": False,
                },
            )
            db.add(q)
            print(f"  Q{order} {gap_id} -> {variants}")

        await db.commit()
        print(
            f"\nDone. Group {group.id} with 7 table_completion gaps seeded into Passage 3."
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
