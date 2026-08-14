"""
Seed IELTS 9, Test 4, Listening Part 4 (Q31-40).

Notes Completion: "Tree planting"
Write ONE WORD ONLY for each answer.

Usage:
    cd backend
    venv\\Scripts\\python scripts\\seed_ielts9_t4_listening_p4.py
"""

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.question import Question
from app.models.question_group import QuestionGroup
from app.models.section import Section, SectionType
from app.models.test import Test

DATABASE_URL = settings.database_url
TEST_TITLE = "Cambridge IELTS 9 \u2013 Test 4"

INSTRUCTION = "Complete the notes below.\nWrite ONE WORD ONLY for each answer."

NOTES_STRUCTURE = {
    "variant": "notes",
    "title": "Tree planting",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "sections": [
        {
            "heading": "Reforestation projects should:",
            "items": [
                {"segments": [{"type": "text", "value": "include a range of tree species"}]},
                {
                    "segments": [
                        {"type": "text", "value": "not include invasive species because of possible "},
                        {"type": "gap", "gap_id": "g1"},
                        {"type": "text", "value": " with native species"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "aim to capture carbon, protect the environment and provide sustainable sources of "},
                        {"type": "gap", "gap_id": "g2"},
                        {"type": "text", "value": " for local people"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "use tree seeds with a high genetic diversity to increase resistance to "},
                        {"type": "gap", "gap_id": "g3"},
                        {"type": "text", "value": " and climate change"},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "plant trees on previously forested land which is in a bad condition, not select land which is being used for "},
                        {"type": "gap", "gap_id": "g4"},
                    ]
                },
            ],
        },
        {
            "heading": "Large-scale reforestation projects",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "Base planning decisions on information from accurate "},
                        {"type": "gap", "gap_id": "g5"},
                        {"type": "text", "value": "."},
                    ]
                },
                {
                    "segments": [
                        {"type": "text", "value": "Drones are useful for identifying areas in Brazil which are endangered by keeping "},
                        {"type": "gap", "gap_id": "g6"},
                        {"type": "text", "value": " and illegal logging."},
                    ]
                },
            ],
        },
        {
            "heading": "Lampang Province, Northern Thailand",
            "items": [
                {"segments": [{"type": "text", "value": "A forest was restored in an area damaged by mining."}]},
                {"segments": [{"type": "text", "value": "A variety of native fig trees were planted, which are important for"}]},
                {"segments": [{"type": "text", "value": "  supporting many wildlife species"}]},
                {
                    "segments": [
                        {"type": "text", "value": "  increasing the "},
                        {"type": "gap", "gap_id": "g7"},
                        {"type": "text", "value": " of recovery by attracting animals and birds, e.g., "},
                        {"type": "gap", "gap_id": "g8"},
                        {"type": "text", "value": " were soon attracted to the area."},
                    ]
                },
            ],
        },
        {
            "heading": "Involving local communities",
            "items": [
                {
                    "segments": [
                        {"type": "text", "value": "Destruction of mangrove forests in Madagascar made it difficult for people to make a living from "},
                        {"type": "gap", "gap_id": "g9"},
                        {"type": "text", "value": "."},
                    ]
                },
                {"segments": [{"type": "text", "value": "The mangrove reforestation project:"}]},
                {"segments": [{"type": "text", "value": "  provided employment for local people"}]},
                {"segments": [{"type": "text", "value": "  restored a healthy ecosystem"}]},
                {
                    "segments": [
                        {"type": "text", "value": "  protects against the higher risk of "},
                        {"type": "gap", "gap_id": "g10"},
                        {"type": "text", "value": "."},
                    ]
                },
            ],
        },
    ],
}

# gap_id -> (order, answer variants)
ANSWERS = [
    ("g1", 31, ["competition"]),
    ("g2", 32, ["income"]),
    ("g3", 33, ["disease", "diseases"]),
    ("g4", 34, ["agriculture"]),
    ("g5", 35, ["maps", "map"]),
    ("g6", 36, ["cattle"]),
    ("g7", 37, ["speed"]),
    ("g8", 38, ["monkeys", "monkey"]),
    ("g9", 39, ["fishing"]),
    ("g10", 40, ["flooding", "floods"]),
]


async def main() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        result = await session.execute(select(Test).where(Test.title == TEST_TITLE))
        test = result.scalar_one_or_none()
        if test is None:
            print(f"ERROR: Test '{TEST_TITLE}' not found.")
            return

        print(f"Found test: {test.title} (id={test.id})")

        existing = await session.execute(
            select(Section).where(
                Section.test_id == test.id,
                Section.type == SectionType.LISTENING,
                Section.order == 4,
            )
        )
        preserved_audio = None
        preserved_script = None
        for old in existing.scalars().all():
            if old.audio_url:
                preserved_audio = old.audio_url
            if old.audioscript:
                preserved_script = old.audioscript
            await session.delete(old)
        await session.flush()

        section = Section(
            id=uuid.uuid4(),
            test_id=test.id,
            type=SectionType.LISTENING,
            order=4,
            title="Part 4 \u2014 Tree Planting",
            audio_url=preserved_audio,
            audioscript=preserved_script,
        )
        session.add(section)
        await session.flush()
        print(f"  Created section: {section.title}")

        group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=1,
            question_type="note_completion",
            instruction=INSTRUCTION,
            options_shared=NOTES_STRUCTURE,
        )
        session.add(group)
        await session.flush()

        for gap_id, order, variants in ANSWERS:
            q = Question(
                id=uuid.uuid4(),
                section_id=section.id,
                question_group_id=group.id,
                order=order,
                question_type="note_completion",
                content={"gap_id": gap_id},
                answer_key={
                    "correct": variants,
                    "max_words": 1,
                    "case_sensitive": False,
                },
            )
            session.add(q)

        await session.flush()
        await session.commit()
        print(f"    Added {len(ANSWERS)} note_completion questions (Q31-40)")
        print("\nDone! Part 4 seeded successfully.")


if __name__ == "__main__":
    asyncio.run(main())
