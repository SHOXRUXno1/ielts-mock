"""Seed Practice Set C Test 5 Speaking, Parts 1-3.

Wording is taken from the printed paper (p.113). Examiner admin questions
(name / nationality) are omitted — the platform already identifies the student.
The teaching tip strips are not part of the exam and are omitted.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_t5_speaking.py
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
from seed_practice_c_common import clear_section, get_section, get_test  # noqa: E402

TEST_NUMBER = 5

PART1_CONTENT = {
    "part": 1,
    "topic": "Work or study and computer games",
    "questions": [
        "Do you work, or are you a student?",
        "How much time do you spend studying each day? Why / Why not?",
        "Do you sometimes work in a group with other students? Why / Why not?",
        "What is the length of your normal working day?",
        "Do you sometimes work in a team? Why / Why not?",
        "Do you prefer playing computer games alone or with a friend? "
        "Why / Why not?",
        "At what age did you first play computer games? Why / Why not?",
        "Do you ever buy computer games for other people? Why / Why not?",
        "In general, are computer games more popular with men or with "
        "women? Why?",
    ],
}

PART2_CONTENT = {
    "part": 2,
    "cue_card": {
        "topic": "the room in your house/apartment which you like best",
        "bullets": [
            "where the room is",
            "what it is used for",
            "what it looks like",
        ],
        "follow_up": "and explain why you like this room best",
    },
    "rounding_off": [
        "Do other people like this room?",
        "Do you spend much time there?",
    ],
}

PART3_CONTENT = {
    "part": 3,
    "topics": [
        "Rooms in general",
        "Interior design",
        "Indoor and outdoor living spaces",
    ],
    "questions": [
        "Which room do families usually spend most time in? Why?",
        "What types of thing do people usually put on the walls of "
        "their rooms?",
        "Is it more important for a room to look nice, or to be "
        "comfortable? Why?",
        "How can different room colours affect the way people feel?",
        "What is modern furniture like compared to older styles of "
        "furniture?",
        "Do you think women are more interested than men in the way "
        "rooms are decorated? Why / Why not?",
        "How might the climate of an area affect the importance of "
        "indoor and outdoor living spaces? Why?",
        "What do you think living spaces will be like in the future? Why?",
    ],
}

PARTS: list[tuple[int, dict, str]] = [
    (30, PART1_CONTENT, "Part 1 \u2014 Work or study and computer games"),
    (
        31,
        PART2_CONTENT,
        "Part 2 \u2014 Describe the room in your house/apartment "
        "which you like best",
    ),
    (
        32,
        PART3_CONTENT,
        "Part 3 \u2014 Rooms, interior design and indoor/outdoor "
        "living spaces",
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
