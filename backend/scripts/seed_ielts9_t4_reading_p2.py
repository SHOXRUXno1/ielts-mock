"""
Seed Reading Passage 2 for Cambridge IELTS 9 – Test 4
(content from Cambridge 19 Test 4 Passage 2 — Deep-sea mining).

Groups:
  1. matching_information Q14-17
  2. matching_features Q18-23 (List of People)
  3. summary_completion Q24-26

Usage:
    cd backend
    venv\\Scripts\\python scripts\\seed_ielts9_t4_reading_p2.py
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
PASSAGE_TITLE = "Deep-sea mining"

MI_INSTRUCTION = (
    "Reading Passage 2 has six paragraphs, A\u2013F.\n"
    "Which paragraph contains the following information?\n"
    "Write the correct letter, A\u2013F, in boxes 14\u201317 on your answer sheet."
)

MI_QUESTIONS = [
    {
        "order": 14,
        "question": (
            "reference to the rapidly increasing need for one raw material "
            "in the transport industry"
        ),
        "correct": "C",
    },
    {
        "order": 15,
        "question": "a rough estimate of the area of the Earth covered by the oceans",
        "correct": "F",
    },
    {
        "order": 16,
        "question": (
            "how a particular underwater habitat, where minerals and organisms "
            "co-exist, is formed"
        ),
        "correct": "E",
    },
    {
        "order": 17,
        "question": (
            "reference to the fact that the countries of the world have yet to "
            "agree on rules for the exploration of the seabed"
        ),
        "correct": "D",
    },
]

MF_INSTRUCTION = (
    "Look at the following statements (Questions 18\u201323) and the list of people below.\n"
    "Match each statement with the correct person or people, A\u2013E.\n"
    "Write the correct letter, A\u2013E, in boxes 18\u201323 on your answer sheet.\n"
    "NB You may use any letter more than once."
)

MF_OPTIONS = [
    "A. Professor Mat Upton",
    "B. Julie Hunter, Julian Aguon and Pradeep Singh",
    "C. Dr Jon Copley",
    "D. Mike Johnston",
    "E. Verena Tunnicliffe",
]

MF_QUESTIONS = [
    {
        "order": 18,
        "question": (
            "A move away from the exploration of heavily mined reserves on land "
            "is a good idea."
        ),
        "correct": "D",
    },
    {
        "order": 19,
        "question": (
            "The negative effects of undersea exploration on local areas and "
            "their inhabitants are being ignored."
        ),
        "correct": "B",
    },
    {
        "order": 20,
        "question": "There are more worthwhile things to extract from the sea than minerals.",
        "correct": "A",
    },
    {
        "order": 21,
        "question": (
            "No other form of human exploration will have such a destructive "
            "impact on marine life as deep-sea mining."
        ),
        "correct": "E",
    },
    {
        "order": 22,
        "question": "More is known about outer space than about what lies beneath the oceans.",
        "correct": "B",
    },
    {
        "order": 23,
        "question": (
            "There is one marine life habitat where experts agree mining "
            "should not take place."
        ),
        "correct": "C",
    },
]

SUMMARY_INSTRUCTION = (
    "Complete the summary below.\n"
    "Choose ONE WORD ONLY from the passage for each answer.\n"
    "Write your answers in boxes 24\u201326 on your answer sheet."
)

SUMMARY_STRUCTURE = {
    "variant": "summary",
    "title": "Mining the sea floor",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "paragraphs": [
        {
            "segments": [
                {
                    "type": "text",
                    "value": (
                        "Mining corporations believe that the mineral resources "
                        "lying under the sea may be superior to those found in "
                        "the earth. They also say that these can be removed "
                        "without producing much "
                    ),
                },
                {"type": "gap", "gap_id": "g1"},
                {"type": "text", "value": "."},
            ]
        },
        {
            "segments": [
                {
                    "type": "text",
                    "value": "The extraction is often done by adapting the ",
                },
                {"type": "gap", "gap_id": "g2"},
                {
                    "type": "text",
                    "value": (
                        " that has already been used to work on land. The method "
                        "of excavation involves removing the seawater from the "
                        "slurry that is brought up to ships and returning it to "
                        "the seabed. However, concerned groups strongly believe "
                        "that "
                    ),
                },
                {"type": "gap", "gap_id": "g3"},
                {
                    "type": "text",
                    "value": (
                        " is necessary due to the possible number of unidentified "
                        "consequences."
                    ),
                },
            ]
        },
    ],
}

SUMMARY_ANSWERS = [
    ("g1", 24, ["waste"]),
    ("g2", 25, ["machinery"]),
    ("g3", 26, ["caution"]),
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

        print(f"Found test: {test.title}")

        # Drop empty reading placeholders
        empty = await session.execute(
            select(Section).where(
                Section.test_id == test.id,
                Section.type == SectionType.READING,
                Section.order == 12,
            )
        )
        for old in empty.scalars().all():
            if not (old.passage or "").strip():
                print(f"  Deleting empty reading section order={old.order}")
                await session.delete(old)
        await session.flush()

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
            print(f"ERROR: Section '{PASSAGE_TITLE}' not found.")
            return

        section.order = 11
        await session.flush()
        print(f"  Using section order={section.order} id={section.id}")

        for g in list(section.question_groups or []):
            for q in list(g.questions or []):
                await session.delete(q)
            await session.flush()
            await session.delete(g)
        await session.flush()

        # ── Q14-17 Matching Information ───────────────────────────────────
        group_mi = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=1,
            question_type="matching_information",
            instruction=MI_INSTRUCTION,
            options_shared={"options": [f"{c}" for c in "ABCDEF"]},
        )
        session.add(group_mi)
        await session.flush()

        for item in MI_QUESTIONS:
            session.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=section.id,
                    question_group_id=group_mi.id,
                    order=item["order"],
                    question_type="matching_information",
                    content={"question": item["question"]},
                    answer_key={"correct": item["correct"]},
                )
            )
        print(f"    Added {len(MI_QUESTIONS)} matching_information (Q14-17)")

        # ── Q18-23 Matching Features ──────────────────────────────────────
        group_mf = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=2,
            question_type="matching_features",
            instruction=MF_INSTRUCTION,
            subtitle="List of People",
            options_shared={
                "options": MF_OPTIONS,
                "options_heading": "List of People",
            },
        )
        session.add(group_mf)
        await session.flush()

        for item in MF_QUESTIONS:
            session.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=section.id,
                    question_group_id=group_mf.id,
                    order=item["order"],
                    question_type="matching_features",
                    content={"question": item["question"]},
                    answer_key={"correct": item["correct"]},
                )
            )
        print(f"    Added {len(MF_QUESTIONS)} matching_features (Q18-23)")

        # ── Q24-26 Summary Completion ─────────────────────────────────────
        group_sum = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=3,
            question_type="summary_completion",
            instruction=SUMMARY_INSTRUCTION,
            options_shared=SUMMARY_STRUCTURE,
        )
        session.add(group_sum)
        await session.flush()

        for gap_id, order, variants in SUMMARY_ANSWERS:
            session.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=section.id,
                    question_group_id=group_sum.id,
                    order=order,
                    question_type="summary_completion",
                    content={"gap_id": gap_id},
                    answer_key=gap_answer_key(variants, max_words=1),
                )
            )
        print(f"    Added {len(SUMMARY_ANSWERS)} summary_completion (Q24-26)")

        await session.commit()
        print("\nDone! Reading Passage 2 seeded successfully.")


if __name__ == "__main__":
    asyncio.run(main())
