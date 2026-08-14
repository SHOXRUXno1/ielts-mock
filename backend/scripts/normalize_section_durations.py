"""Reset section durations to the IELTS recommendation.

    cd backend
    venv\\Scripts\\python scripts\\normalize_section_durations.py --test-id=<uuid>
    venv\\Scripts\\python scripts\\normalize_section_durations.py --all --dry-run
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
from app.models.test_section_settings import TestSectionSettings
from app.services.section_duration import recommended_for
from app.services.section_settings import TYPE_ORDER


def _fmt(minutes: int | None) -> str:
    return "untimed" if minutes is None else f"{minutes} min"


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test-id", help="Normalize a single test (UUID).")
    group.add_argument("--all", action="store_true", help="Normalize every test.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the changes without writing them.",
    )
    args = parser.parse_args()

    async with async_session() as db:
        stmt = select(Test).options(selectinload(Test.section_settings)).order_by(Test.title)
        if args.test_id:
            stmt = stmt.where(Test.id == args.test_id)
        tests = (await db.execute(stmt)).scalars().unique().all()

        if not tests:
            print("No matching tests.")
            await engine.dispose()
            return

        changed = 0
        for test in tests:
            by_type = {s.section_type: s for s in test.section_settings}
            lines: list[str] = []
            for section_type in TYPE_ORDER:
                recommended = recommended_for(section_type)
                row = by_type.get(section_type)
                if row is None:
                    lines.append(f"  {section_type.capitalize():<10} created -> {_fmt(recommended)}")
                    test.section_settings.append(
                        TestSectionSettings(
                            test_id=test.id,
                            section_type=section_type,
                            duration_minutes=recommended,
                        )
                    )
                    continue
                if row.duration_minutes == recommended:
                    continue
                lines.append(
                    f"  {section_type.capitalize():<10} "
                    f"{_fmt(row.duration_minutes)} -> {_fmt(recommended)}"
                )
                row.duration_minutes = recommended

            if lines:
                changed += 1
                print(f'\nTest "{test.title}" (id={test.id}):')
                print("\n".join(lines))

        if not changed:
            print("Nothing to change — all durations already match the recommendation.")
        elif args.dry_run:
            await db.rollback()
            print(f"\nDry run: {changed} test(s) would be updated.")
        else:
            await db.commit()
            print(f"\nUpdated {changed} test(s).")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
