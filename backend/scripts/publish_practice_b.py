"""Publish a Practice Set B test, refusing to publish a broken one.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\publish_practice_b.py 1
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.api.tests import _collect_publish_errors, _load_test_detail  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.models.test import Test  # noqa: E402
from seed_practice_b_common import BOOK_SLUG  # noqa: E402


async def publish(db: AsyncSession, test_number: int) -> int:
    row = (
        await db.execute(
            select(Test).where(
                Test.book_slug == BOOK_SLUG, Test.test_number == test_number
            )
        )
    ).scalar_one_or_none()
    if row is None:
        print(f"test {test_number} not found")
        return 1

    detail = await _load_test_detail(db, row.id)
    errors = _collect_publish_errors(detail)
    if errors:
        print(f"refusing to publish {row.title}:")
        for error in errors:
            print(f"  - {error}")
        return 1

    if row.is_published:
        print(f"{row.title} was already published")
        return 0

    row.is_published = True
    await db.commit()
    print(f"published {row.title} ({row.id})")
    return 0


async def main() -> int:
    test_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        code = await publish(db, test_number)
    await engine.dispose()
    return code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
