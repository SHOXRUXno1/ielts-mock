"""Seed Practice Set A Test 5 Speaking, Parts 1-3.

Part 1: your country, then Libraries, then Team Sports.
Part 2: describe a place that you like.
Part 3: Places of Interest, then The Environment.

The paper offers two topics in Parts 1 and 3; both are kept, which is how a real
examiner works through the part.

Idempotent: each part section is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t5_speaking.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.models.question import Question, QuestionType  # noqa: E402
from app.models.question_group import QuestionGroup  # noqa: E402
from app.models.section import SectionType  # noqa: E402
from seed_practice_a_common import clear_section, get_section, get_test  # noqa: E402

TEST_NUMBER = 5

PART1_CONTENT = {
    "part": 1,
    "topic": "Libraries / Team Sports",
    "questions": [
        "Tell me a little about your country.",
        "What are some of the good things and some of the bad things about "
        "living in your country?",
        "Where would be your favourite place to live in your country? (Why?)",
        "Do you ever go to libraries? (Why/Why not?)",
        "Do you think libraries should be free or that people should have to "
        "pay to use them?",
        "How can we get more people to use libraries?",
        "Do you think government money for libraries could be spent on better "
        "things?",
        "Do you play or watch a team sport? (Why/Why not?)",
        "Why do you think people like playing or watching team sports?",
        "What are some of the disadvantages of playing or watching team sports?",
        "How can we encourage younger people to play more sport?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a place that you like",
        "bullets": [
            "where this place is",
            "when you first went there",
            "what you do or did there",
        ],
        "follow_up": "and explain why this place is so special for you",
    },
}

PART3_CONTENT = {
    "part": 3,
    "topics": ["Places of Interest", "The Environment"],
    "questions": [
        "What kinds of places in your country are threatened by building or "
        "other types of progress?",
        "Do you think it is important to preserve historical areas in "
        "countries? (Why?)",
        "How can governments protect places of interest?",
        "What sort of places will be of interest to people in the future?",
        "What kinds of pollution problems does your country face?",
        "How can ordinary people help fight pollution?",
        "Do you think that there should be stricter punishments for people and "
        "companies that pollute the environment?",
        "What sort of pollution problems do you think the world will face in "
        "the future?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 — Your country, libraries, team sports"),
    (31, PART2_CONTENT, "Part 2 — A place that you like"),
    (32, PART3_CONTENT, "Part 3 — Places of interest, the environment"),
]


async def seed(db: AsyncSession) -> None:
    test = await get_test(db, TEST_NUMBER)
    print(f"Test: {test.title} ({test.id})")

    for order, content, label in PARTS:
        section = await get_section(db, test.id, SectionType.SPEAKING, order)
        removed = await clear_section(db, section.id)
        section.title = label

        group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section.id,
            order=1,
            question_type=QuestionType.SPEAKING_PART.value,
            instruction="",
            options_shared=None,
        )
        db.add(group)
        await db.flush()

        db.add(
            Question(
                id=uuid.uuid4(),
                section_id=section.id,
                question_group_id=group.id,
                order=1,
                question_type=QuestionType.SPEAKING_PART,
                content=content,
                answer_key=None,
            )
        )
        prompts = (
            len(content["questions"])
            if "questions" in content
            else len(content["cue_card"]["bullets"])
        )
        print(f"  {label}  removed {removed} old row(s)  {prompts} prompts")

    await db.commit()
    print("\nDone. Speaking Parts 1-3 seeded.")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
