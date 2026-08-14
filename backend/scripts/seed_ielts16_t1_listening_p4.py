"""Seed IELTS 16 Test 1 Listening Part 4 — Stoicism.

Q31-40: note_completion (ONE WORD ONLY)

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_ielts16_t1_listening_p4.py
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
PART4_ID = uuid.UUID("de5cd9d8-f485-4c22-a02e-eb32e80dd509")

INSTRUCTION = (
    "Complete the notes below.\n"
    "Write ONE WORD ONLY for each answer."
)

STRUCTURE: dict = {
    "variant": "notes",
    "title": "Stoicism",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "Stoicism is still relevant today "
                                "because of its "
                            ),
                        },
                        {"type": "gap", "gap_id": "g1"},
                        {"type": "text", "value": " appeal."},
                    ]
                },
            ],
        },
        {
            "heading": "Ancient Stoics",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "Stoicism was founded over 2,000 years "
                                "ago in Greece."
                            ),
                        }
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "The Stoics' ideas are surprisingly "
                                "well known, despite not being "
                                "intended for "
                            ),
                        },
                        {"type": "gap", "gap_id": "g2"},
                        {"type": "text", "value": "."},
                    ]
                },
            ],
        },
        {
            "heading": "Stoic principles",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "Happiness could be achieved by "
                                "leading a virtuous life."
                            ),
                        }
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "Controlling emotions was essential.",
                        }
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "Epictetus said that external events "
                                "cannot be controlled but the "
                            ),
                        },
                        {"type": "gap", "gap_id": "g3"},
                        {
                            "type": "text",
                            "value": (
                                " people make in response can be "
                                "controlled."
                            ),
                        },
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "A Stoic is someone who has a different "
                                "view on experiences which others "
                                "would consider as "
                            ),
                        },
                        {"type": "gap", "gap_id": "g4"},
                        {"type": "text", "value": "."},
                    ]
                },
            ],
        },
        {
            "heading": "The influence of Stoicism",
            "items": [
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "George Washington organised a ",
                        },
                        {"type": "gap", "gap_id": "g5"},
                        {
                            "type": "text",
                            "value": " about Cato to motivate his men.",
                        },
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "The French artist Delacroix was a Stoic.",
                        }
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "Adam Smith's ideas on ",
                        },
                        {"type": "gap", "gap_id": "g6"},
                        {
                            "type": "text",
                            "value": " were influenced by Stoicism.",
                        },
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "Some of today's political leaders "
                                "are inspired by the Stoics."
                            ),
                        }
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "Cognitive Behaviour Therapy (CBT)",
                        }
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "the treatment for "},
                        {"type": "gap", "gap_id": "g7"},
                        {
                            "type": "text",
                            "value": " is based on ideas from Stoicism",
                        },
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": "people learn to base their thinking on ",
                        },
                        {"type": "gap", "gap_id": "g8"},
                        {"type": "text", "value": "."},
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "In business, people benefit from "
                                "Stoicism by identifying obstacles as "
                            ),
                        },
                        {"type": "gap", "gap_id": "g9"},
                        {"type": "text", "value": "."},
                    ]
                },
            ],
        },
        {
            "heading": "Relevance of Stoicism",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "It requires a lot of "},
                        {"type": "gap", "gap_id": "g10"},
                        {
                            "type": "text",
                            "value": (
                                " but Stoicism can help people to "
                                "lead a good life."
                            ),
                        },
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "value": (
                                "It teaches people that having a "
                                "strong character is more important "
                                "than anything else."
                            ),
                        }
                    ]
                },
            ],
        },
    ],
}

ANSWERS: list[tuple[str, list[str]]] = [
    ("g1", ["practical"]),
    ("g2", ["publication"]),
    ("g3", ["choices"]),
    ("g4", ["negative"]),
    ("g5", ["play"]),
    ("g6", ["capitalism"]),
    ("g7", ["depression"]),
    ("g8", ["logic"]),
    ("g9", ["opportunity"]),
    ("g10", ["practice", "practise"]),
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

        section.title = "Part 4 — Stoicism"
        print(f"Test: {test.title} #{getattr(test, 'test_number', '?')}")
        print(f"Section: Listening Part {section.order} ({section.id})")
        if section.audio_url:
            print(f"Keeping audio_url: {section.audio_url}")

        removed = await delete_compound_groups(
            db,
            section_id=PART4_ID,
            question_types=("note_completion",),
            title="Stoicism",
        )
        if removed:
            print(f"Removed {removed} previous group/question row(s)")

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

        for i, (gap_id, variants) in enumerate(ANSWERS, start=1):
            q = Question(
                id=uuid.uuid4(),
                section_id=PART4_ID,
                question_group_id=group.id,
                order=i,
                question_type=QuestionType.NOTE_COMPLETION,
                content={"gap_id": gap_id},
                answer_key=gap_answer_key(variants, max_words=1),
            )
            db.add(q)
            print(f"  Q{30 + i} {gap_id} -> {variants}")

        await db.commit()
        print(
            f"\nDone. Group {group.id} with 10 note_completion gaps "
            "seeded into Part 4."
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
