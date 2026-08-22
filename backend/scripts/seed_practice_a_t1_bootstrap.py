"""Create the Practice Set A book and its first test, ready for content.

Makes the Test row, the eleven standard sections and the timing settings — the
same shape the admin wizard produces — then points the four listening sections
at their audio files. Content itself comes from the per-skill seed scripts.

Left unpublished on purpose: publishing before the questions are checked would
put a half-built exam in front of a candidate.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_a_t1_bootstrap.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.models.section import Section, SectionType  # noqa: E402
from app.models.test import Test  # noqa: E402
from app.services import section_settings as settings_service  # noqa: E402
from seed_practice_a_common import AUDIO_URL, BOOK_NAME, BOOK_SLUG  # noqa: E402

TEST_NUMBER = 1
TITLE = f"{BOOK_NAME} — Test {TEST_NUMBER}"
DESCRIPTION = "Academic practice test: Listening, Reading, Writing and Speaking."

# (type, order) exactly as app.api.tests.DEFAULT_SECTIONS lays them out.
SECTION_PLAN: list[tuple[SectionType, int]] = [
    (SectionType.LISTENING, 1),
    (SectionType.LISTENING, 2),
    (SectionType.LISTENING, 3),
    (SectionType.LISTENING, 4),
    (SectionType.READING, 10),
    (SectionType.READING, 11),
    (SectionType.READING, 12),
    (SectionType.WRITING, 20),
    (SectionType.SPEAKING, 30),
    (SectionType.SPEAKING, 31),
    (SectionType.SPEAKING, 32),
]

SECTION_TITLES: dict[tuple[SectionType, int], str] = {
    (SectionType.LISTENING, 1): "Part 1 — Lost property report",
    (SectionType.LISTENING, 2): "Part 2 — Welcome speech for new students",
    (SectionType.LISTENING, 3): "Part 3 — Two students discussing the new term",
    (SectionType.LISTENING, 4): "Part 4 — Oil tankers and oil slicks",
    (SectionType.READING, 10): "Passage 1 — The big cats at the Sharjah Breeding Centre",
    (SectionType.READING, 11): "Passage 2 — Insomnia: the enemy of sleep",
    (SectionType.READING, 12): "Passage 3 — Alternative farming methods in Oregon",
}


async def seed(db: AsyncSession) -> None:
    test = (
        await db.execute(
            select(Test).where(
                Test.book_slug == BOOK_SLUG, Test.test_number == TEST_NUMBER
            )
        )
    ).scalar_one_or_none()

    if test is None:
        test = Test(
            id=uuid.uuid4(),
            title=TITLE,
            description=DESCRIPTION,
            is_published=False,
            type="academic",
            book_name=BOOK_NAME,
            book_slug=BOOK_SLUG,
            test_number=TEST_NUMBER,
        )
        db.add(test)
        await db.flush()
        db.add_all(settings_service.build_default_rows(test.id))
        print(f"created test {test.id}")
    else:
        print(f"test already exists: {test.id}")

    existing = {
        (s.type if isinstance(s.type, SectionType) else SectionType(s.type), s.order): s
        for s in (
            await db.execute(select(Section).where(Section.test_id == test.id))
        ).scalars().all()
    }

    listening_part = 0
    for section_type, order in SECTION_PLAN:
        section = existing.get((section_type, order))
        if section is None:
            section = Section(
                id=uuid.uuid4(),
                test_id=test.id,
                type=section_type,
                order=order,
            )
            db.add(section)
            await db.flush()
            action = "created"
        else:
            action = "kept   "

        title = SECTION_TITLES.get((section_type, order))
        if title:
            section.title = title

        if section_type is SectionType.LISTENING:
            listening_part += 1
            section.audio_url = AUDIO_URL.format(test=TEST_NUMBER, part=listening_part)

        detail = f" audio={section.audio_url}" if section.audio_url else ""
        print(f"  {action} {section_type.value:<9} order={order:<3}{detail}")

    await db.commit()
    print(
        f"\nDone. {BOOK_NAME} Test {TEST_NUMBER} is ready for content.\n"
        "Next: seed listening, reading, writing and speaking, then publish."
    )


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
