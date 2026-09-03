"""Seed Practice Set E Test 1 Speaking, Parts 1-3.

Source: Peter May Oxford IELTS Practice Tests, Test 1 (pp.36-38).
Exam questions only — no "Improve your skills" exercises, no
"predicting questions" student activities, no strategy boxes.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_e_t1_speaking.py
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
from seed_practice_e_common import clear_section, get_section, get_test  # noqa: E402

TEST_NUMBER = 1

PART1_CONTENT = {
    "part": 1,
    "topic": "Where you grew up / Spare time / Travel",
    "questions": [
        "What kind of town is it?",
        "What\u2019s the most interesting area?",
        "What kinds of jobs do people do there?",
        "Do you think it\u2019s a good place to live?",
        "Do you have any hobbies or interests?",
        "How did you first become interested in that?",
        "What other things like that would you like to do?",
        "What kinds of transport do you use regularly?",
        "How do people in your country travel on long journeys?",
        "How has transport there changed over the last twenty-five years?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "someone you know, or somebody famous, who has achieved great success",
        "bullets": [
            "who they are and what they do",
            "where they come from: their background",
            "how they became successful",
        ],
        "follow_up": "and explain why you admire this person",
    },
    "rounding_off": [
        "Has this person had to make sacrifices in order to achieve success?",
        "Do most people in your country share your admiration for him/her?",
    ],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Personal success",
        "Winning and losing",
        "The competitive society",
    ],
    "questions": [
        "How does present-day society measure the success of an individual?",
        "How can we ensure that more people achieve their aims in life?",
        "Would you rather be successful in your job or in your social life?",
        "Which is more important in sport: winning or taking part?",
        "What makes some sports people take drugs to improve their performance?",
        "Why are some countries more successful than others in events such as "
        "the Olympics?",
        "How do competitive relationships between people differ from "
        "cooperative relationships?",
        "In what ways has society become more competitive in the last "
        "twenty years?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 \u2014 Where you grew up"),
    (
        31,
        PART2_CONTENT,
        "Part 2 \u2014 Describe someone who has achieved great success",
    ),
    (
        32,
        PART3_CONTENT,
        "Part 3 \u2014 Personal success, winning and losing",
    ),
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
        print(f"  {label}  removed {removed} old row(s)")

    await db.commit()
    print("\nDone. Speaking seeded (Parts 1\u20133).")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
