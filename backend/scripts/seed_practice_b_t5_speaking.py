"""Seed Practice Set B Test 5 Speaking, Parts 1-3.

Wording is taken from the printed paper (p.127). Examiner admin questions
(name / nationality) are omitted — the platform already identifies the student.
The teaching tip strips on p.127 are not part of the exam and are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_b_t5_speaking.py
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

TEST_NUMBER = 5

PART1_CONTENT = {
    "part": 1,
    "topic": "Studies, work and clothes",
    "questions": [
        "Are you a student or do you have a job?",
        "What qualifications do you hope to get from your studies?",
        "What qualifications did you have to have for your job?",
        "Do you meet many people in your job / studies? Why / Why not?",
        "What kind of clothes do you wear for work / college?",
        "Do you prefer wearing formal or casual clothes? Why?",
        "Do you like to get clothes as gifts from friends or family? "
        "Why / Why not?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a family event you are looking forward to",
        "bullets": [
            "what the event is",
            "where it will be held",
            "what you will do at this event",
        ],
        "follow_up": "and explain why you are looking forward to this family event",
    },
    "rounding_off": [
        "Did you help to plan this event?",
        "Does your family often have special events?",
    ],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Family celebrations",
        "Recent social changes",
    ],
    "questions": [
        "What type of special occasions are generally celebrated in your "
        "country?",
        "How important is it for families to celebrate occasions together? Why?",
        "Are family occasions as important today as they were for former "
        "generations?",
        "How has the role of elderly people in the family changed in recent "
        "times?",
        "Who has more power and influence in the family today, young people "
        "or grandparents?",
        "In the future what kind of units or groups will people live in, do "
        "you think?",
        "What impact have modern lifestyles had on neighbourhood communities? "
        "Why?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 — Studies, work and clothes"),
    (
        31,
        PART2_CONTENT,
        "Part 2 — A family event you are looking forward to",
    ),
    (32, PART3_CONTENT, "Part 3 — Family celebrations and social change"),
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
