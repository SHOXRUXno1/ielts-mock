"""
Seed IELTS 9, Test 4, Listening Part 2 (Q11-20).

Creates:
  - Listening Section (Part 2) on existing "Cambridge IELTS 9 – Test 4"
  - 4 question groups: 2x multi_select, 1x matching, 2x mcq

Usage:
    cd backend
    venv\\Scripts\\python scripts\\seed_ielts9_t4_listening_p2.py
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
#  Questions data
# ─────────────────────────────────────────────────────────────────────────────

QUESTIONS = [
    # Q11-12: Multi-select — problems with training programmes
    {
        "order": 11,
        "type": "multi_select",
        "group": "problems",
        "answer": ["A", "E"],
        "content": {
            "question": "Which TWO problems with some training programmes for new runners does Liz mention?",
            "options": [
                "There is a risk of serious injury.",
                "They are unsuitable for certain age groups.",
                "They are unsuitable for people with health issues.",
                "It is difficult to stay motivated.",
                "There is a lack of individual support.",
            ],
            "choose_n": 2,
            "display_slot_end": 12,
        },
    },

    # Q13-14: Multi-select — tips for new runners
    {
        "order": 13,
        "type": "multi_select",
        "group": "tips",
        "answer": ["A", "C"],
        "content": {
            "question": "Which TWO tips does Liz recommend for new runners?",
            "options": [
                "doing two runs a week",
                "running in the evening",
                "going on runs with a friend",
                "listening to music during runs",
                "running very slowly",
            ],
            "choose_n": 2,
            "display_slot_end": 14,
        },
    },

    # Q15-18: Matching — reasons for not joining club
    {
        "order": 15,
        "type": "matching",
        "group": "matching",
        "answer": "A",
        "content": {"stem": "Gen"},
    },
    {
        "order": 16,
        "type": "matching",
        "group": "matching",
        "answer": "C",
        "content": {"stem": "James"},
    },
    {
        "order": 17,
        "type": "matching",
        "group": "matching",
        "answer": "B",
        "content": {"stem": "Leo"},
    },
    {
        "order": 18,
        "type": "matching",
        "group": "matching",
        "answer": "C",
        "content": {"stem": "Mark"},
    },

    # Q19: MCQ — Liz's first marathon
    {
        "order": 19,
        "type": "mcq",
        "group": "mcq",
        "answer": "C",
        "content": {
            "question": "What does Liz say about running her first marathon?",
            "options": [
                "It has always been her ambition.",
                "Her husband persuaded her to do it.",
                "She nearly gave up before the end.",
            ],
        },
    },

    # Q20: MCQ — signing up for a race
    {
        "order": 20,
        "type": "mcq",
        "group": "mcq",
        "answer": "B",
        "content": {
            "question": "Liz says new runners should sign up for a race",
            "options": [
                "every six months.",
                "within a few weeks of taking up running.",
                "after completing several practice runs.",
            ],
        },
    },
]


async def main() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        # Find existing test
        result = await session.execute(select(Test).where(Test.title == TEST_TITLE))
        test = result.scalar_one_or_none()
        if test is None:
            print(f"ERROR: Test '{TEST_TITLE}' not found. Run seed_ielts9_t4_listening_p1.py first.")
            return

        print(f"Found test: {test.title} (id={test.id})")

        # Delete existing Part 2 if re-seeding
        existing = await session.execute(
            select(Section).where(
                Section.test_id == test.id,
                Section.type == SectionType.LISTENING,
                Section.order == 2,
            )
        )
        preserved_audio_url = None
        preserved_audioscript = None
        for old in existing.scalars().all():
            if old.audio_url:
                preserved_audio_url = old.audio_url
            if old.audioscript:
                preserved_audioscript = old.audioscript
            await session.delete(old)
        await session.flush()

        # Create Part 2 section
        section = Section(
            id=uuid.uuid4(),
            test_id=test.id,
            type=SectionType.LISTENING,
            order=2,
            title="Part 2 \u2014 Running Programme",
            audio_url=preserved_audio_url,
            audioscript=preserved_audioscript,
        )
        session.add(section)
        await session.flush()
        print(f"  Created section: {section.title} (id={section.id})")

        # ── Group 1: Multi-select Q11-12 ─────────────────────────────────
        group_problems = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=1,
            question_type="multi_select",
            instruction="Choose TWO letters, A\u2013E.",
        )
        session.add(group_problems)

        # ── Group 2: Multi-select Q13-14 ─────────────────────────────────
        group_tips = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=2,
            question_type="multi_select",
            instruction="Choose TWO letters, A\u2013E.",
        )
        session.add(group_tips)

        # ── Group 3: Matching Q15-18 ─────────────────────────────────────
        group_matching = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=3,
            question_type="matching",
            instruction="What reason prevented each of the following members of the Compton Park Runners Club from joining until recently?\nChoose the correct letter, A\u2013C, next to Questions 15\u201318.",
            subtitle="Club members",
            options_shared={
                "options": [
                    "A. a lack of confidence",
                    "B. a dislike of running",
                    "C. a lack of time",
                ],
                "options_heading": "Reasons",
            },
        )
        session.add(group_matching)

        # ── Group 4: MCQ Q19-20 ──────────────────────────────────────────
        group_mcq = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=4,
            question_type="mcq",
            instruction="Choose the correct letter, A, B or C.",
        )
        session.add(group_mcq)
        await session.flush()

        # ── Create questions ──────────────────────────────────────────────
        group_map = {
            "problems": group_problems.id,
            "tips": group_tips.id,
            "matching": group_matching.id,
            "mcq": group_mcq.id,
        }

        for q_data in QUESTIONS:
            gid = group_map[q_data["group"]]
            content = q_data.get("content", {})
            answer = q_data["answer"]
            answer_key = {"correct": answer}

            question = Question(
                id=uuid.uuid4(),
                section_id=section.id,
                question_group_id=gid,
                question_type=q_data["type"],
                order=q_data["order"],
                content=content,
                answer_key=answer_key,
            )
            session.add(question)

        await session.commit()
        print(f"  Created {len(QUESTIONS)} questions")
        print("Done!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
