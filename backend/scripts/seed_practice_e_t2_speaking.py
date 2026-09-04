"""Seed Practice Set E Test 2 Speaking, Parts 1-3.

Source: Peter May Oxford IELTS Practice Tests, Test 2 (pp.67-69).
Exam questions only — no "Improve your skills" exercises, no
strategy boxes, no communication-strategy matching activities.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_e_t2_speaking.py
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

TEST_NUMBER = 2

PART1_CONTENT = {
    "part": 1,
    "topic": "Family / Food and eating / The news media",
    "questions": [
        "Is your family small or quite large?",
        "What do you do when you are all together?",
        "Which of them do you get on with best? Why?",
        "What are your favourite foods?",
        "Is there anything you never eat?",
        "Where do you normally eat? Why?",
        "In what ways are people\u2019s eating habits changing these days?",
        "Where do you normally get your news from?",
        "How do you think news reporting in your country differs "
        "from that abroad?",
        "Tell me about an interesting news item you\u2019ve read or "
        "heard recently.",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "a music video or a concert that has made an impression on you",
        "bullets": [
            "which kind of music it was and who performed it",
            "what it was like musically",
            "what it was like visually",
        ],
        "follow_up": "and explain why you liked or disliked it",
    },
    "rounding_off": [
        "When and where did you see it?",
        "Have you ever seen anything else similar to it?",
    ],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Music in the world",
        "The psychology of music",
        "Changes in music",
    ],
    "questions": [
        "Why is pop music so popular globally?",
        "Which do you prefer: traditional music from your country "
        "or classical music from abroad?",
        "How do different kinds of music affect the way people feel?",
        "What is the best music to listen to while studying?",
        "What are the main differences between music today and "
        "that of previous decades?",
        "Which contributes more to the success of modern singers "
        "and bands: their music, or their appearance and image? "
        "Why do you think so?",
        "What kinds of music will people be listening to ten years "
        "from now?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 \u2014 Family, food, and news"),
    (
        31,
        PART2_CONTENT,
        "Part 2 \u2014 Describe a music video or concert",
    ),
    (
        32,
        PART3_CONTENT,
        "Part 3 \u2014 Music in the world",
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
