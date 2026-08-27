"""Seed Practice Set B Test 1 Speaking, Parts 1-3.

Wording is taken from the printed paper (p.37). Examiner admin questions
(name / nationality) are omitted — the platform already identifies the student.
The teaching tip strips on p.36 are not part of the exam and are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t1_speaking.py
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

TEST_NUMBER = 1

PART1_CONTENT = {
    "part": 1,
    "topic": "Computers and the Internet",
    "questions": [
        "How often do you use the computer? What for?",
        "Do you like using the Internet? Why / Why not?",
        "How did you learn to use a computer?",
        "Do you think it is important to know how to use a computer? Why / Why not?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a typical day at work, school or college",
        "bullets": [
            "what you do",
            "when you do it",
            "how long you've had this routine",
        ],
        "follow_up": "and explain what you would like to change in your work or study routine",
    },
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "How people feel about routines",
        "Choice in routines",
        "Changes in routines",
    ],
    "questions": [
        "Do young people and old people have different attitudes to routines where you live?",
        "What are the benefits and drawbacks of having a daily routine?",
        "What factors influence most people's daily routines?",
        "Do you think people get enough choice in their daily routines? Why / Why not?",
        "How are work or study schedules today different from those in the past? Why?",
        "Is this a positive or negative development? Why?",
        "How do you think people's routines and schedules will change in the future?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 — Computers and the Internet"),
    (31, PART2_CONTENT, "Part 2 — A typical day at work, school or college"),
    (32, PART3_CONTENT, "Part 3 — Routines"),
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
