"""Seed Practice Set A Test 1 Speaking, Parts 1-3.

Part 1: family, then Health and Exercise, then Music.
Part 2: describe a favourite film or television programme.
Part 3: TV and Radio, then Films and Cinema.

The paper offers two topics in Parts 1 and 3; both are kept, which is how a real
examiner works through the part.

Idempotent: each part section is cleared before it is written.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t1_speaking.py
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

TEST_NUMBER = 1

PART1_CONTENT = {
    "part": 1,
    "topic": "Health and Exercise / Music",
    "questions": [
        "Tell me about your family.",
        "Where do they live?",
        "What do you like doing when you are with your family?",
        "What sorts of things do you do to keep healthy?",
        "What other sorts of things are popular in your country to keep healthy?",
        "What sorts of exercise do you not like doing?",
        "How can we get young people to do more exercise?",
        "What is your favourite type of music and why?",
        "Do you think that a country's traditional music is important for its "
        "culture? [Why?]",
        "Why do people's tastes in music often change as they get older?",
        "What are some of the different uses of music in your country?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "your favourite film or television programme",
        "bullets": [
            "when you watch it",
            "who is in it",
            "what happens in it",
        ],
        "follow_up": "and explain why you particularly like it",
    },
}

PART3_CONTENT = {
    "part": 3,
    "topics": ["TV and Radio", "Films and Cinema"],
    "questions": [
        "Why do you think television has become so popular over the last 50 years?",
        "Do you think that there is still a future for radio with television "
        "being so popular?",
        "Which is better for presenting the news: television or radio? [Why?]",
        "How can we stop young people today watching too much television?",
        "Can you compare television and cinema as forms of entertainment?",
        "Do people in your country prefer American films or films from their "
        "part of the world?",
        "How do you think world cinema will develop over the next 50 years?",
        "Do you feel that film stars are overpaid for what they do?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 — Family, health and exercise, music"),
    (31, PART2_CONTENT, "Part 2 — A favourite film or television programme"),
    (32, PART3_CONTENT, "Part 3 — TV and radio, films and cinema"),
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
