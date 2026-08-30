"""Seed Practice Set B Test 2 Speaking, Parts 1-3.

Wording is taken from the printed paper (p.65). Examiner admin questions
(name / nationality) are omitted — the platform already identifies the student.
The teaching tip strips on p.64 are not part of the exam and are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t2_speaking.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.models.question import Question, QuestionType  # noqa: E402
from app.models.question_group import QuestionGroup  # noqa: E402
from app.models.section import SectionType  # noqa: E402
from seed_practice_b_common import clear_section, get_section, get_test  # noqa: E402

TEST_NUMBER = 2

PART1_CONTENT = {
    "part": 1,
    "topic": "Work or studies, and free time",
    "questions": [
        "What do you do?",
        "Why did you choose this job or subject?",
        "What job would you like to do in the future? Why?",
        "What skills do you need for that job?",
        "What do you enjoy doing in your free time?",
        "Do you think you get enough free time? Why or why not?",
        "How important is it to use your free time usefully?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a part of the world you would like to visit",
        "bullets": [
            "where it is",
            "how and what you know about it",
            "what you would like to do there",
        ],
        "follow_up": "and explain why you would like to visit this part of the world",
    },
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "International tourism",
        "The effects of tourism",
    ],
    "questions": [
        "Why do you think people want to visit other countries?",
        "What makes some places very attractive to tourists?",
        "Do people travel abroad more or less than they did in the past? Why or why not?",
        "Will international tourism increase or decrease in the future? Why?",
        "How can tourism benefit local people and places?",
        "Are there any drawbacks of tourism?",
        "Does tourism help to promote international understanding? Why or why not?",
        "How reliable is tourism as an industry?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 — Work or studies, and free time"),
    (31, PART2_CONTENT, "Part 2 — A part of the world you would like to visit"),
    (32, PART3_CONTENT, "Part 3 — International tourism"),
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
