"""
Seed IELTS 9, Test 4, Listening Part 1 (Q1-10).

Creates:
  - Test "Cambridge IELTS 9 – Test 4" (if not exists)
  - Listening Section (Part 1)
  - 3 question groups (table_completion, multi_select, table_completion)
  - 10 questions

Uses the NEW compound format:
  - question_type = "table_completion" (not "table")
  - table structure lives in group.options_shared (not in each question content)
  - questions reference gap_id only

Usage:
    cd backend
    venv\\Scripts\\python scripts\\seed_ielts9_t4_listening_p1.py
"""

import asyncio
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section, SectionType
from app.models.test import Test

DATABASE_URL = settings.database_url
TEST_TITLE = "Cambridge IELTS 9 \u2013 Test 4"

# ─────────────────────────────────────────────────────────────────────────────
#  Table structure for Q1-4: Health Centres
#  Format: options_shared with variant="table", segments model
# ─────────────────────────────────────────────────────────────────────────────

HEALTH_TABLE_STRUCTURE = {
    "variant": "table",
    "title": "Health Centres",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "headers": ["Name of centre", "Doctor\u2019s name", "Advantage"],
    "rows": [
        # Row 1: The Harvey Clinic | Dr Green (example) | especially good with _1_ (babies)
        [
            {"variant": "plain", "segments": [{"type": "text", "value": "The Harvey Clinic"}]},
            {"variant": "plain", "segments": [{"type": "text", "value": "(Example) Dr Green"}]},
            {"variant": "plain", "segments": [
                {"type": "text", "value": "especially good with "},
                {"type": "gap", "gap_id": "1"},
            ]},
        ],
        # Row 2: The _2_ Health Practice | Dr Fuller | offers _3_ appointments
        [
            {"variant": "plain", "segments": [
                {"type": "text", "value": "The "},
                {"type": "gap", "gap_id": "2"},
                {"type": "text", "value": " Health Practice"},
            ]},
            {"variant": "plain", "segments": [{"type": "text", "value": "Dr Fuller"}]},
            {"variant": "plain", "segments": [
                {"type": "text", "value": "offers "},
                {"type": "gap", "gap_id": "3"},
                {"type": "text", "value": " appointments"},
            ]},
        ],
        # Row 3: The Shore Lane Health Centre | Dr _4_ | (empty)
        [
            {"variant": "plain", "segments": [{"type": "text", "value": "The Shore Lane Health Centre"}]},
            {"variant": "plain", "segments": [
                {"type": "text", "value": "Dr "},
                {"type": "gap", "gap_id": "4"},
            ]},
            {"variant": "plain", "segments": [{"type": "text", "value": ""}]},
        ],
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
#  Table structure for Q7-10: Talks for patients
# ─────────────────────────────────────────────────────────────────────────────

TALKS_TABLE_STRUCTURE = {
    "variant": "table",
    "title": "Talks for patients at Shore Lane Health Centre",
    "instruction_words": "NO MORE THAN TWO WORDS AND/OR A NUMBER",
    "max_words_per_gap": 2,
    "headers": ["Subject of talk", "Date/Time", "Location", "Notes"],
    "rows": [
        # Giving up smoking | 25th Feb 7pm | room 4 | useful for people with asthma or _7_ problems
        [
            {"variant": "plain", "segments": [{"type": "text", "value": "Giving up smoking"}]},
            {"variant": "plain", "segments": [{"type": "text", "value": "25th February 7 pm"}]},
            {"variant": "plain", "segments": [{"type": "text", "value": "room 4"}]},
            {"variant": "plain", "segments": [
                {"type": "text", "value": "useful for people with asthma or "},
                {"type": "gap", "gap_id": "7"},
                {"type": "text", "value": " problems"},
            ]},
        ],
        # Healthy eating | 1st March at 5 pm | the _8_ (Shore Lane) | anyone welcome
        [
            {"variant": "plain", "segments": [{"type": "text", "value": "Healthy eating"}]},
            {"variant": "plain", "segments": [{"type": "text", "value": "1st March at 5 pm"}]},
            {"variant": "plain", "segments": [
                {"type": "text", "value": "the "},
                {"type": "gap", "gap_id": "8"},
                {"type": "text", "value": " (Shore Lane)"},
            ]},
            {"variant": "plain", "segments": [{"type": "text", "value": "anyone welcome"}]},
        ],
        # Avoiding injuries during exercise | 9th March at _9_ | room 6 | for all _10_
        [
            {"variant": "plain", "segments": [{"type": "text", "value": "Avoiding injuries during exercise"}]},
            {"variant": "plain", "segments": [
                {"type": "text", "value": "9th March at "},
                {"type": "gap", "gap_id": "9"},
            ]},
            {"variant": "plain", "segments": [{"type": "text", "value": "room 6"}]},
            {"variant": "plain", "segments": [
                {"type": "text", "value": "for all "},
                {"type": "gap", "gap_id": "10"},
            ]},
        ],
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
#  Questions data
# ─────────────────────────────────────────────────────────────────────────────

QUESTIONS = [
    # Q1-4: Table completion (gap_id references)
    {"order": 1, "type": "table_completion", "group": "health", "gap_id": "1", "answer": "babies"},
    {"order": 2, "type": "table_completion", "group": "health", "gap_id": "2", "answer": "Eshool"},
    {"order": 3, "type": "table_completion", "group": "health", "gap_id": "3", "answer": "evening"},
    {"order": 4, "type": "table_completion", "group": "health", "gap_id": "4", "answer": ["Gormley", "GORMLEY"]},

    # Q5-6: Multi-select (single question, choose 2)
    {
        "order": 5,
        "type": "multi_select",
        "group": "multi",
        "answer": ["B", "E"],
        "content": {
            "question": "Which TWO of the following are offered free of charge at Shore Lane Health Centre?",
            "options": [
                "acupuncture",
                "employment medicals",
                "sports injury therapy",
                "travel advice",
                "vaccinations",
            ],
            "choose_n": 2,
            "display_slot_end": 6,
        },
    },

    # Q7-10: Table completion (gap_id references)
    {"order": 7, "type": "table_completion", "group": "talks", "gap_id": "7", "answer": ["heart", "heart disease"]},
    {"order": 8, "type": "table_completion", "group": "talks", "gap_id": "8", "answer": "primary school"},
    {"order": 9, "type": "table_completion", "group": "talks", "gap_id": "9", "answer": ["$n/a", "unavailable"]},
    {"order": 10, "type": "table_completion", "group": "talks", "gap_id": "10", "answer": ["ages", "age groups"]},
]


async def main() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        # Find or create the test
        result = await session.execute(select(Test).where(Test.title == TEST_TITLE))
        test = result.scalar_one_or_none()
        if test is None:
            test = Test(
                id=uuid.uuid4(),
                title=TEST_TITLE,
                description="Cambridge IELTS 9, Academic Test 4",
                is_published=True,
                book_slug="cambridge-ielts-9",
                book_name="Cambridge IELTS 9",
                test_number=4,
            )
            session.add(test)
            await session.flush()
            print(f"Created test: {test.title} (id={test.id})")
        else:
            print(f"Found existing test: {test.title} (id={test.id})")

        # Delete existing listening Part 1, but preserve audio/audioscript
        existing_sections = await session.execute(
            select(Section).where(
                Section.test_id == test.id,
                Section.type == SectionType.LISTENING,
                Section.order == 1,
            )
        )
        preserved_audio_url = None
        preserved_audioscript = None
        for old_section in existing_sections.scalars().all():
            if old_section.audio_url:
                preserved_audio_url = old_section.audio_url
            if old_section.audioscript:
                preserved_audioscript = old_section.audioscript
            await session.delete(old_section)
        await session.flush()

        # Create listening section (Part 1)
        section = Section(
            id=uuid.uuid4(),
            test_id=test.id,
            type=SectionType.LISTENING,
            order=1,
            title="Part 1 \u2014 Health Centre Enquiry",
            audio_url=preserved_audio_url,
            audioscript=preserved_audioscript,
        )
        session.add(section)
        await session.flush()
        print(f"  Created section: {section.title} (id={section.id})")
        if preserved_audio_url:
            print(f"  Preserved audio_url: {preserved_audio_url}")

        # ── Group 1: Table Completion — Health Centres (Q1-4) ──────────────
        group_health = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=1,
            question_type="table_completion",
            instruction="Complete the table below.\nWrite ONE WORD ONLY for each answer.",
            options_shared=HEALTH_TABLE_STRUCTURE,
        )
        session.add(group_health)

        # ── Group 2: Multi-select (Q5-6) ──────────────────────────────────
        group_multi = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=2,
            question_type="multi_select",
            instruction="Choose TWO letters, A\u2013E.",
        )
        session.add(group_multi)

        # ── Group 3: Table Completion — Talks (Q7-10) ─────────────────────
        group_talks = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=3,
            question_type="table_completion",
            instruction="Complete the table below.\nWrite NO MORE THAN TWO WORDS AND/OR A NUMBER for each answer.",
            options_shared=TALKS_TABLE_STRUCTURE,
        )
        session.add(group_talks)
        await session.flush()

        # ── Create questions ──────────────────────────────────────────────
        group_map = {
            "health": group_health.id,
            "multi": group_multi.id,
            "talks": group_talks.id,
        }

        for q_data in QUESTIONS:
            gid = group_map[q_data["group"]]

            # Use explicit content if provided, otherwise build from gap_id
            if "content" in q_data:
                content = q_data["content"]
            else:
                content: dict = {}
                if "gap_id" in q_data:
                    content["gap_id"] = q_data["gap_id"]

            # Build answer_key
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
