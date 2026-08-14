"""
Seed Reading Passage 3 for Cambridge IELTS 9 – Test 4
(content from Cambridge 19 Test 4 Passage 3 — The Unselfish Gene).

Groups:
  1. mcq Q27-30
  2. summary_completion Q31-35
  3. yes_no_ng Q36-40

Usage:
    cd backend
    venv\\Scripts\\python scripts\\seed_ielts9_t4_reading_p3.py
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
PASSAGE_TITLE = "The Unselfish Gene"

MCQ_INSTRUCTION = "Choose the correct letter, A, B, C or D."

MCQ_QUESTIONS = [
    {
        "order": 27,
        "question": "What is the writer doing in the first paragraph?",
        "options": [
            "setting out two opposing views about human nature",
            "justifying his opinion about our tendency to be greedy",
            "describing a commonly held belief about people\u2019s behaviour",
            "explaining why he thinks that humans act in a selfish manner",
        ],
        "correct": "C",
    },
    {
        "order": 28,
        "question": "What point is made about Richard Dawkins\u2019 book The Selfish Gene?",
        "options": [
            "Its appeal lay in the radical nature of its ideas.",
            "Its success was due to the scientific support it offered.",
            "It presented a view that was in line with the attitudes of its time.",
            "It took an innovative approach to the analysis of human psychology.",
        ],
        "correct": "C",
    },
    {
        "order": 29,
        "question": (
            "What does the writer suggest about the prehistoric era "
            "in the fourth paragraph?"
        ),
        "options": [
            "Societies were more complex than many people believe.",
            "Supplies of natural resources were probably relatively plentiful.",
            "Most estimates about population sizes are likely to be inaccurate.",
            "Humans moved across continents more than was previously thought.",
        ],
        "correct": "B",
    },
    {
        "order": 30,
        "question": (
            "The writer refers to Bruce Knauft\u2019s work as support "
            "for the idea that"
        ),
        "options": [
            "selfishness is a relatively recent development in human societies.",
            "only people in isolated communities can live in an unselfish manner.",
            "very few lifestyles have survived unchanged since prehistoric times.",
            "hunter-gatherer cultures worldwide are declining in number.",
        ],
        "correct": "A",
    },
]

SUMMARY_INSTRUCTION = (
    "Complete the summary below.\n"
    "Choose ONE WORD ONLY from the passage for each answer.\n"
    "Write your answers in boxes 31\u201335 on your answer sheet."
)

SUMMARY_STRUCTURE = {
    "variant": "summary",
    "title": "Contemporary hunter-gatherer societies",
    "instruction_words": "ONE WORD ONLY",
    "max_words_per_gap": 1,
    "paragraphs": [
        {
            "segments": [
                {
                    "type": "text",
                    "value": (
                        "Bruce Knauft\u2019s research shows that contemporary "
                        "hunter-gatherer societies tend to exhibit a high level of "
                    ),
                },
                {"type": "gap", "gap_id": "g1"},
                {
                    "type": "text",
                    "value": (
                        " in all areas of life. In these cultures, distributing "
                        "resources fairly among all members is a moral obligation. "
                        "These societies also employ strategies to prevent "
                        "differences in "
                    ),
                },
                {"type": "gap", "gap_id": "g2"},
                {
                    "type": "text",
                    "value": (
                        " occurring: for example, the !Kung follow a custom "
                        "whereby the credit for one person\u2019s success at "
                    ),
                },
                {"type": "gap", "gap_id": "g3"},
                {
                    "type": "text",
                    "value": (
                        " is given to another member of the group. Individuals "
                        "who behave in a "
                    ),
                },
                {"type": "gap", "gap_id": "g4"},
                {
                    "type": "text",
                    "value": (
                        " manner are punished by being excluded from the group, "
                        "and women have a considerable amount of "
                    ),
                },
                {"type": "gap", "gap_id": "g5"},
                {
                    "type": "text",
                    "value": " in choices regarding work and marriage.",
                },
            ]
        }
    ],
}

SUMMARY_ANSWERS = [
    ("g1", 31, ["egalitarianism"]),
    ("g2", 32, ["status"]),
    ("g3", 33, ["hunting"]),
    ("g4", 34, ["domineering"]),
    ("g5", 35, ["autonomy"]),
]

YNNG_INSTRUCTION = (
    "Do the following statements agree with the claims of the writer "
    "in Reading Passage 3?\n"
    "In boxes 36\u201340 on your answer sheet, choose"
)

YNNG_QUESTIONS = [
    {
        "order": 36,
        "statement": (
            "Some anthropologists are mistaken about the point when the number "
            "of societies such as the !Kung began to decline."
        ),
        "correct": "Not Given",
    },
    {
        "order": 37,
        "statement": (
            "Humans who developed warlike traits in prehistory would have had "
            "an advantage over those who did not."
        ),
        "correct": "No",
    },
    {
        "order": 38,
        "statement": (
            "Being peaceful and cooperative is a natural way for people to behave."
        ),
        "correct": "Yes",
    },
    {
        "order": 39,
        "statement": (
            "Negative traits are more apparent in some modern cultures than in others."
        ),
        "correct": "Not Given",
    },
    {
        "order": 40,
        "statement": (
            "Animal research has failed to reveal a link between changes in the "
            "environment and the emergence of aggressive tendencies."
        ),
        "correct": "No",
    },
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

        section.order = 12
        await session.flush()
        print(f"  Using section order={section.order} id={section.id}")

        for g in list(section.question_groups or []):
            for q in list(g.questions or []):
                await session.delete(q)
            await session.flush()
            await session.delete(g)
        await session.flush()

        # ── Q27-30 MCQ ────────────────────────────────────────────────────
        group_mcq = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=1,
            question_type="mcq",
            instruction=MCQ_INSTRUCTION,
        )
        session.add(group_mcq)
        await session.flush()

        for item in MCQ_QUESTIONS:
            session.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=section.id,
                    question_group_id=group_mcq.id,
                    order=item["order"],
                    question_type="mcq",
                    content={
                        "question": item["question"],
                        "options": item["options"],
                    },
                    answer_key={"correct": item["correct"]},
                )
            )
        print(f"    Added {len(MCQ_QUESTIONS)} MCQ (Q27-30)")

        # ── Q31-35 Summary ────────────────────────────────────────────────
        group_sum = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=2,
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
        print(f"    Added {len(SUMMARY_ANSWERS)} summary_completion (Q31-35)")

        # ── Q36-40 Yes/No/NG ──────────────────────────────────────────────
        group_yn = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=3,
            question_type="yes_no_ng",
            instruction=YNNG_INSTRUCTION,
        )
        session.add(group_yn)
        await session.flush()

        for item in YNNG_QUESTIONS:
            session.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=section.id,
                    question_group_id=group_yn.id,
                    order=item["order"],
                    question_type="yes_no_ng",
                    content={"statement": item["statement"]},
                    answer_key={"correct": item["correct"]},
                )
            )
        print(f"    Added {len(YNNG_QUESTIONS)} yes_no_ng (Q36-40)")

        await session.commit()
        print("\nDone! Reading Passage 3 seeded successfully.")


if __name__ == "__main__":
    asyncio.run(main())
