"""
Seed IELTS 9, Test 4, Listening Part 3 (Q21-25) + Part 4 (Q26-30).

Part 3: 5x MCQ (Choose A, B or C)
Part 4: Matching — Location of books (A-G)

Usage:
    cd backend
    venv\\Scripts\\python scripts\\seed_ielts9_t4_listening_p3_p4.py
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

# ─────────────────────────────────────────────────────────────────────────────
#  Part 3: Questions 21-25 (MCQ)
# ─────────────────────────────────────────────────────────────────────────────

PART3_QUESTIONS = [
    {
        "order": 21,
        "answer": "A",
        "content": {
            "question": "Kieran thinks the packing advice given by Jane\u2019s grandfather is",
            "options": [
                "common sense.",
                "hard to follow.",
                "over-protective.",
            ],
        },
    },
    {
        "order": 22,
        "answer": "C",
        "content": {
            "question": "How does Jane feel about the books her grandfather has given her?",
            "options": [
                "They are not worth keeping.",
                "They should go to a collector.",
                "They have sentimental value for her.",
            ],
        },
    },
    {
        "order": 23,
        "answer": "A",
        "content": {
            "question": "Jane and Kieran agree that hardback books should be",
            "options": [
                "put out on display.",
                "given as gifts to visitors.",
                "more attractively designed.",
            ],
        },
    },
    {
        "order": 24,
        "answer": "B",
        "content": {
            "question": "While talking about taking a book from a shelf, Jane",
            "options": [
                "describes the mistakes other people make doing it.",
                "reflects on a significant childhood experience.",
                "explains why some books are easier to remove than others.",
            ],
        },
    },
    {
        "order": 25,
        "answer": "C",
        "content": {
            "question": "What do Jane and Kieran suggest about new books?",
            "options": [
                "Their parents liked buying them as presents.",
                "They would like to buy more of them.",
                "Not everyone can afford them.",
            ],
        },
    },
]

# ─────────────────────────────────────────────────────────────────────────────
#  Part 4: Questions 26-30 (Matching — Location of books)
# ─────────────────────────────────────────────────────────────────────────────

PART4_OPTIONS = [
    "A. near the entrance",
    "B. in the attic",
    "C. at the back of the shop",
    "D. on a high shelf",
    "E. near the stairs",
    "F. in a specially designed space",
    "G. within the caf\u00e9",
]

PART4_QUESTIONS = [
    {"order": 26, "answer": "F", "content": {"stem": "rare books"}},
    {"order": 27, "answer": "E", "content": {"stem": "children\u2019s books"}},
    {"order": 28, "answer": "B", "content": {"stem": "unwanted books"}},
    {"order": 29, "answer": "A", "content": {"stem": "requested books"}},
    {"order": 30, "answer": "D", "content": {"stem": "coursebooks"}},
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

        # ── Part 3 ────────────────────────────────────────────────────────────
        existing = await session.execute(
            select(Section).where(
                Section.test_id == test.id,
                Section.type == SectionType.LISTENING,
                Section.order == 3,
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

        section3 = Section(
            id=uuid.uuid4(),
            test_id=test.id,
            type=SectionType.LISTENING,
            order=3,
            title="Part 3 \u2014 Books and Reading",
            audio_url=preserved_audio,
            audioscript=preserved_script,
        )
        session.add(section3)
        await session.flush()
        print(f"  Created section: {section3.title}")

        group_mcq = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section3.id,
            order=1,
            question_type="mcq",
            instruction="Choose the correct letter, A, B or C.",
        )
        session.add(group_mcq)
        await session.flush()

        for q_data in PART3_QUESTIONS:
            q = Question(
                id=uuid.uuid4(),
                section_id=section3.id,
                question_group_id=group_mcq.id,
                order=q_data["order"],
                question_type="mcq",
                content=q_data["content"],
                answer_key={"answer": q_data["answer"]},
            )
            session.add(q)

        await session.flush()
        print(f"    Added {len(PART3_QUESTIONS)} MCQ questions (Q21-25)")

        # ── Part 4 ────────────────────────────────────────────────────────────
        existing4 = await session.execute(
            select(Section).where(
                Section.test_id == test.id,
                Section.type == SectionType.LISTENING,
                Section.order == 4,
            )
        )
        preserved_audio4 = None
        preserved_script4 = None
        for old in existing4.scalars().all():
            if old.audio_url:
                preserved_audio4 = old.audio_url
            if old.audioscript:
                preserved_script4 = old.audioscript
            await session.delete(old)
        await session.flush()

        section4 = Section(
            id=uuid.uuid4(),
            test_id=test.id,
            type=SectionType.LISTENING,
            order=4,
            title="Part 4 \u2014 Second-hand Bookshop",
            audio_url=preserved_audio4,
            audioscript=preserved_script4,
        )
        session.add(section4)
        await session.flush()
        print(f"  Created section: {section4.title}")

        group_matching = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section4.id,
            order=1,
            question_type="matching",
            instruction="Where does Jane\u2019s grandfather keep each of the following types of books in his shop?\nChoose the correct letter, A\u2013G, next to Questions 26\u201330.",
            subtitle="Types of books",
            options_shared={
                "options": PART4_OPTIONS,
                "options_heading": "Location of books",
            },
        )
        session.add(group_matching)
        await session.flush()

        for q_data in PART4_QUESTIONS:
            q = Question(
                id=uuid.uuid4(),
                section_id=section4.id,
                question_group_id=group_matching.id,
                order=q_data["order"],
                question_type="matching",
                content=q_data["content"],
                answer_key={"answer": q_data["answer"]},
            )
            session.add(q)

        await session.flush()
        print(f"    Added {len(PART4_QUESTIONS)} matching questions (Q26-30)")

        await session.commit()
        print("\nDone! Parts 3 & 4 seeded successfully.")


if __name__ == "__main__":
    asyncio.run(main())
