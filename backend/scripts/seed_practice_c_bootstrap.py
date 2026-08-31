"""Create one Practice Set C test with its eleven empty sections.

Section titles come from sections.json in the test's data directory.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\seed_practice_c_bootstrap.py 1
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.models.section import Section, SectionType  # noqa: E402
from app.models.test import Test  # noqa: E402
from app.services import section_settings as settings_service  # noqa: E402
from seed_practice_c_common import (  # noqa: E402
    AUDIO_URL,
    BOOK_NAME,
    BOOK_SLUG,
    data_dir,
)

DEFAULT_DESCRIPTION = (
    "Academic practice test: Listening, Reading, Writing and Speaking."
)

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


def load_plan(test_number: int) -> tuple[str, dict[str, str]]:
    path = data_dir(test_number) / "sections.json"
    if not path.exists():
        return DEFAULT_DESCRIPTION, {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw.get("description") or DEFAULT_DESCRIPTION, raw.get("titles") or {}


async def seed(db: AsyncSession, test_number: int) -> None:
    description, titles = load_plan(test_number)

    test = (
        await db.execute(
            select(Test).where(
                Test.book_slug == BOOK_SLUG, Test.test_number == test_number
            )
        )
    ).scalar_one_or_none()

    if test is None:
        test = Test(
            id=uuid.uuid4(),
            title=f"{BOOK_NAME} — Test {test_number}",
            description=description,
            is_published=False,
            type="academic",
            book_name=BOOK_NAME,
            book_slug=BOOK_SLUG,
            test_number=test_number,
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

        title = titles.get(f"{section_type.value}:{order}")
        if title:
            section.title = title

        if section_type is SectionType.LISTENING:
            listening_part += 1
            section.audio_url = AUDIO_URL.format(test=test_number, part=listening_part)

        detail = f" audio={section.audio_url}" if section.audio_url else ""
        print(f"  {action} {section_type.value:<9} order={order:<3}{detail}")

    await db.commit()
    print(
        f"\nDone. {BOOK_NAME} Test {test_number} is ready for content.\n"
        "Next: seed listening, reading, writing and speaking, then publish."
    )


async def main() -> None:
    test_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        await seed(db, test_number)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
