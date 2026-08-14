"""Report tests whose section durations differ from the IELTS recommendation.

Read-only — nothing is written. Use normalize_section_durations.py to fix.

    cd backend
    venv\\Scripts\\python scripts\\check_section_durations.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import async_session, engine
from app.models.test import Test
from app.services.section_duration import (
    DurationRangeError,
    check_duration,
    recommended_for,
)
from app.services.section_settings import TYPE_ORDER


def _classify(section_type: str, minutes: int | None) -> tuple[str, str] | None:
    """Return (severity, message) when the value is not the recommendation."""
    recommended = recommended_for(section_type)
    try:
        warning = check_duration(section_type, minutes)
    except DurationRangeError as exc:
        return "out of range", str(exc)
    if warning is None:
        return None
    shown = "untimed" if minutes is None else f"{minutes} min"
    expected = "untimed" if recommended is None else f"{recommended} min"
    return "within range", f"{shown} (recommended {expected}) - may be intentional"


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--test-id",
        help="Only inspect one test (UUID).",
    )
    args = parser.parse_args()

    async with async_session() as db:
        stmt = select(Test).options(selectinload(Test.section_settings)).order_by(Test.title)
        if args.test_id:
            stmt = stmt.where(Test.id == args.test_id)
        tests = (await db.execute(stmt)).scalars().unique().all()

    flagged = 0
    for test in tests:
        by_type = {s.section_type: s.duration_minutes for s in test.section_settings}
        problems: list[tuple[str, str, str]] = []
        for section_type in TYPE_ORDER:
            if section_type not in by_type:
                problems.append((section_type, "missing", "no settings row"))
                continue
            verdict = _classify(section_type, by_type[section_type])
            if verdict is not None:
                problems.append((section_type, verdict[0], verdict[1]))

        if not problems:
            continue

        flagged += 1
        print(f'\nTest "{test.title}" (id={test.id}):')
        for section_type, severity, message in problems:
            print(f"  {section_type.capitalize():<10} [{severity}] {message}")
        print(f"  Fix: python scripts/normalize_section_durations.py --test-id={test.id}")

    if flagged:
        print(f"\n{flagged} test(s) with non-recommended durations.")
    else:
        print("All section durations match the recommendation.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
