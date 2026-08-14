"""Report (and optionally fix) Listening durations that are not 30 min.

Defaults to a read-only report. Apply changes only after confirmation.

    cd backend
    venv\\Scripts\\python scripts\\normalize_listening_duration.py
    venv\\Scripts\\python scripts\\normalize_listening_duration.py --apply
    venv\\Scripts\\python scripts\\normalize_listening_duration.py --apply --yes
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

LISTENING = "listening"
TARGET = recommended_for(LISTENING)  # 30


def _fmt(minutes: int | None) -> str:
    return "untimed" if minutes is None else f"{minutes} min"


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--test-id",
        help="Only inspect/fix one test (UUID).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write listening duration=30 after confirmation.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the interactive confirmation (use with --apply).",
    )
    args = parser.parse_args()

    async with async_session() as db:
        stmt = (
            select(Test)
            .options(selectinload(Test.section_settings))
            .order_by(Test.title)
        )
        if args.test_id:
            stmt = stmt.where(Test.id == args.test_id)
        tests = (await db.execute(stmt)).scalars().unique().all()

        if not tests:
            print("No matching tests.")
            await engine.dispose()
            return

        to_fix: list[tuple[Test, TestSectionSettings | None, int | None]] = []
        for test in tests:
            by_type = {s.section_type: s for s in test.section_settings}
            row = by_type.get(LISTENING)
            current = row.duration_minutes if row is not None else None
            if row is None or current != TARGET:
                to_fix.append((test, row, current))

        if not to_fix:
            print("All listening durations are already 30 min.")
            await engine.dispose()
            return

        print("Listening durations that differ from recommended 30 min:\n")
        for test, _row, current in to_fix:
            print(
                f'  Test "{test.title}" (id={test.id}): '
                f"{_fmt(current)} -> {_fmt(TARGET)}"
            )
        print(f"\n{len(to_fix)} test(s) listed.")

        if not args.apply:
            print(
                "\nReport only. Re-run with --apply to migrate "
                "(add --yes to skip the prompt)."
            )
            await engine.dispose()
            return

        if not args.yes:
            answer = input("\nProceed and set listening to 30 min? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                print("Aborted.")
                await engine.dispose()
                return

        for test, row, _current in to_fix:
            if row is None:
                test.section_settings.append(
                    TestSectionSettings(
                        test_id=test.id,
                        section_type=LISTENING,
                        duration_minutes=TARGET,
                    )
                )
            else:
                row.duration_minutes = TARGET

        await db.commit()
        print(f"\nUpdated listening duration on {len(to_fix)} test(s).")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
