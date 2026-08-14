"""Seed Listening Part 3 MCQ (Q21-30) into IELTS 11 test."""

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

INSTRUCTION = "Choose the correct letter, A, B or C."
SUBTITLE = "Study on Gender in Physics"

QUESTIONS: list[dict] = [
    {
        "order": 1,
        "question": "The students in Akira Miyake's study were all majoring in",
        "options": [
            "physics.",
            "psychology or physics.",
            "science, technology, engineering or mathematics.",
        ],
        "correct": "C",
    },
    {
        "order": 2,
        "question": "The aim of Miyake's study was to investigate",
        "options": [
            "what kind of women choose to study physics.",
            "a way of improving women's performance in physics.",
            "whether fewer women than men study physics at college.",
        ],
        "correct": "B",
    },
    {
        "order": 3,
        "question": "The female physics students were wrong to believe that",
        "options": [
            "the teachers marked them in an unfair way.",
            "the male students expected them to do badly.",
            "their test results were lower than the male students'.",
        ],
        "correct": "B",
    },
    {
        "order": 4,
        "question": "Miyake's team asked the students to write about",
        "options": [
            "what they enjoyed about studying physics.",
            "the successful experiences of other people.",
            "something that was important to them personally.",
        ],
        "correct": "C",
    },
    {
        "order": 5,
        "question": "What was the aim of the writing exercise done by the subjects?",
        "options": [
            "to reduce stress",
            "to strengthen verbal ability",
            "to encourage logical thinking",
        ],
        "correct": "A",
    },
    {
        "order": 6,
        "question": "What surprised the researchers about the study?",
        "options": [
            "how few students managed to get A grades",
            "the positive impact it had on physics results for women",
            "the difference between male and female performance",
        ],
        "correct": "B",
    },
    {
        "order": 7,
        "question": "Greg and Lisa think Miyake's results could have been affected by",
        "options": [
            "the length of the writing task.",
            "the number of students who took part.",
            "the information the students were given.",
        ],
        "correct": "C",
    },
    {
        "order": 8,
        "question": "Greg and Lisa decide that in their own project, they will compare the effects of",
        "options": [
            "two different writing tasks.",
            "a writing task with an oral task.",
            "two different oral tasks.",
        ],
        "correct": "A",
    },
    {
        "order": 9,
        "question": "The main finding of Smolinsky's research was that class teamwork activities",
        "options": [
            "were most effective when done by all-women groups.",
            "had no effect on the performance of men or women.",
            "improved the results of men more than of women.",
        ],
        "correct": "B",
    },
    {
        "order": 10,
        "question": "What will Lisa and Greg do next?",
        "options": [
            "talk to a professor",
            "observe a science class",
            "look at the science timetable",
        ],
        "correct": "A",
    },
]


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")

        result = await db.execute(
            select(Section)
            .options(selectinload(Section.question_groups).selectinload(QuestionGroup.questions))
            .where(Section.test_id == TEST_ID, Section.type == "listening")
            .order_by(Section.order)
        )
        listening = list(result.scalars().all())
        print(f"Found {len(listening)} listening section(s) for {test.title}")
        for s in listening:
            n_groups = len(s.question_groups or [])
            n_qs = sum(len(g.questions or []) for g in (s.question_groups or []))
            print(f"  Part order={s.order} id={s.id} groups={n_groups} questions={n_qs}")

        # Part 3 = 3rd listening section by order (1-based part index)
        if len(listening) < 3:
            raise SystemExit(
                f"Need at least 3 listening parts; found {len(listening)}. "
                "Create Listening Part 3 first."
            )

        part3 = sorted(listening, key=lambda s: s.order)[2]
        print(f"\nUsing Part 3 section id={part3.id} order={part3.order}")

        # Remove existing MCQ groups that look like this set (idempotent re-seed)
        existing_mcq = [
            g
            for g in (part3.question_groups or [])
            if str(getattr(g.question_type, "value", g.question_type)) == "mcq"
            and (g.subtitle or "").strip() == SUBTITLE
        ]
        if existing_mcq:
            for g in existing_mcq:
                print(f"Deleting existing group {g.id} ({len(g.questions or [])} questions)")
                await db.delete(g)
            await db.flush()

        remaining = await db.execute(
            select(QuestionGroup).where(QuestionGroup.section_id == part3.id)
        )
        remaining_groups = list(remaining.scalars().all())
        max_group_order = max((g.order for g in remaining_groups), default=0)

        group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=part3.id,
            order=max_group_order + 1,
            question_type=QuestionType.MCQ.value,
            instruction=INSTRUCTION,
            subtitle=SUBTITLE,
            options_shared=None,
        )
        db.add(group)
        await db.flush()

        # Section-level question order: continue after existing questions in this section
        q_result = await db.execute(
            select(Question).where(Question.section_id == part3.id)
        )
        existing_qs = list(q_result.scalars().all())
        next_order = max((q.order for q in existing_qs), default=0) + 1

        for item in QUESTIONS:
            q = Question(
                id=uuid.uuid4(),
                section_id=part3.id,
                question_group_id=group.id,
                order=next_order,
                question_type=QuestionType.MCQ,
                content={
                    "question": item["question"],
                    "options": item["options"],
                },
                answer_key={"correct": item["correct"]},
            )
            db.add(q)
            print(f"  Q{20 + item['order']} order={next_order} -> {item['correct']}")
            next_order += 1

        await db.commit()
        print(f"\nDone. Group {group.id} with 10 MCQ questions seeded into Part 3.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
