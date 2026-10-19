"""Refuse a full reseed if a Practice Set F test has been used or published."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.models.attempt import Attempt  # noqa: E402
from app.models.test import Test  # noqa: E402
from seed_practice_f_common import BOOK_SLUG  # noqa: E402


async def main(test_number: int) -> None:
    engine = create_async_engine(settings.database_url)
    try:
        async with AsyncSession(engine) as db:
            test = (await db.execute(select(Test).where(
                Test.book_slug == BOOK_SLUG, Test.test_number == test_number,
            ))).scalar_one_or_none()
            if test is not None:
                attempts = (await db.execute(select(func.count()).select_from(Attempt).where(
                    Attempt.test_id == test.id,
                ))).scalar_one()
                if test.is_published or attempts:
                    raise SystemExit(
                        f"Refusing to reseed {test.title}: published={test.is_published}, "
                        f"attempts={attempts}. Existing student data must be preserved."
                    )
            print(f"Practice Set F Test {test_number}: safe to seed unpublished content")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1])))
