"""Seed IELTS 16 Test 1 Listening Part 3 — Art project (Jess & Tom).

Q21-22 / Q23-24: multi_select (choose TWO)
Q25-30: matching_features (personal meanings A-H)

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_ielts16_t1_listening_p3.py
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.models.question import Question, QuestionType
from app.models.question_group import QuestionGroup
from app.models.section import Section
from app.models.test import Test
from app.services.seed_compound import next_group_order

TEST_ID = uuid.UUID("4cdab44f-db90-4122-a02b-d7df41fc400a")  # Ielts 16
PART3_ID = uuid.UUID("48020a6f-0d0f-423a-b4ca-0d6d467ee213")

MULTI_INSTRUCTION = "Choose TWO letters, A-E."

MULTI_ITEMS: list[dict] = [
    {
        "question": (
            "Which TWO parts of the introductory stage to their art "
            "projects do Jess and Tom agree were useful?"
        ),
        "options": [
            "the Bird Park visit",
            "the workshop sessions",
            "the Natural History Museum visit",
            "the projects done in previous years",
            "the handouts with research sources",
        ],
        "correct": ["C", "E"],
    },
    {
        "question": (
            "Which TWO ways do both Jess and Tom decide to change "
            "their proposals?"
        ),
        "options": [
            "by giving a rationale for their action plans",
            "by being less specific about the outcome",
            "by adding a video diary presentation",
            "by providing a timeline and a mind map",
            "by making their notes more evaluative",
        ],
        "correct": ["B", "E"],
    },
]

MATCH_INSTRUCTION = (
    "Which personal meaning do the students decide to give to each "
    "of the following pictures?\n"
    "Choose the correct letter, A-H, next to Questions 25-30."
)

MATCH_OPTIONS = [
    "A. a childhood memory",
    "B. hope for the future",
    "C. fast movement",
    "D. a potential threat",
    "E. the power of colour",
    "F. the continuity of life",
    "G. protection of nature",
    "H. a confused attitude to nature",
]

MATCH_ITEMS: list[tuple[str, str]] = [
    ("Falcon (Landseer)", "D"),
    ("Fish hawk (Audubon)", "C"),
    ("Kingfisher (van Gogh)", "A"),
    ("Portrait of William Wells", "H"),
    ("Vairumati (Gauguin)", "F"),
    ("Portrait of Giovanni de Medici", "G"),
]


async def _wipe(db: AsyncSession) -> int:
    """Delete Part 3 groups/questions; answers cascade (do not null question_id)."""
    from sqlalchemy import delete as sa_delete

    from app.models.answer import Answer

    qids = (
        await db.execute(select(Question.id).where(Question.section_id == PART3_ID))
    ).scalars().all()
    if qids:
        await db.execute(sa_delete(Answer).where(Answer.question_id.in_(qids)))
        await db.flush()

    groups = (
        await db.execute(
            select(QuestionGroup).where(QuestionGroup.section_id == PART3_ID)
        )
    ).scalars().all()
    n = 0
    for g in groups:
        qs = (
            await db.execute(
                select(Question).where(Question.question_group_id == g.id)
            )
        ).scalars().all()
        for q in qs:
            await db.delete(q)
        await db.flush()
        await db.delete(g)
        n += 1
    leftovers = (
        await db.execute(select(Question).where(Question.section_id == PART3_ID))
    ).scalars().all()
    for q in leftovers:
        await db.delete(q)
        n += 1
    if n:
        await db.flush()
    return n


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        test = await db.get(Test, TEST_ID)
        if test is None:
            raise SystemExit(f"Test {TEST_ID} not found")

        section = await db.get(Section, PART3_ID)
        if section is None or section.test_id != TEST_ID:
            raise SystemExit(f"Part 3 section {PART3_ID} not found")

        section.title = "Part 3 — Art project"
        print(f"Test: {test.title} #{getattr(test, 'test_number', '?')}")
        print(f"Section: Listening Part {section.order} ({section.id})")
        if section.audio_url:
            print(f"Keeping audio_url: {section.audio_url}")

        removed = await _wipe(db)
        if removed:
            print(f"Removed {removed} previous group/question row(s)")

        group_order = await next_group_order(db, PART3_ID)
        order = 1

        for item in MULTI_ITEMS:
            g = QuestionGroup(
                id=uuid.uuid4(),
                section_id=PART3_ID,
                order=group_order,
                question_type=QuestionType.MULTI_SELECT.value,
                instruction=MULTI_INSTRUCTION,
                subtitle=None,
                options_shared=None,
            )
            db.add(g)
            await db.flush()
            group_order += 1

            q = Question(
                id=uuid.uuid4(),
                section_id=PART3_ID,
                question_group_id=g.id,
                order=order,
                question_type=QuestionType.MULTI_SELECT,
                content={
                    "choose_n": 2,
                    "question": item["question"],
                    "options": item["options"],
                },
                answer_key={"correct": item["correct"]},
            )
            db.add(q)
            print(f"  multi_select order={order} -> {item['correct']}")
            order += 1

        match_group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=PART3_ID,
            order=group_order,
            question_type=QuestionType.MATCHING_FEATURES.value,
            instruction=MATCH_INSTRUCTION,
            subtitle="Personal meanings",
            options_shared={
                "options": MATCH_OPTIONS,
                "questions_heading": "Pictures",
            },
        )
        db.add(match_group)
        await db.flush()

        for stem, letter in MATCH_ITEMS:
            q = Question(
                id=uuid.uuid4(),
                section_id=PART3_ID,
                question_group_id=match_group.id,
                order=order,
                question_type=QuestionType.MATCHING_FEATURES,
                content={"question": stem},
                answer_key={"correct": letter},
            )
            db.add(q)
            print(f"  matching order={order} {stem!r} -> {letter}")
            order += 1

        await db.commit()
        print(
            "\nDone. Part 3 seeded: 2 multi_select (4 slots) + "
            "6 matching_features."
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
