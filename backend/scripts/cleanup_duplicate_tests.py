"""Find tests that share the same title (possible duplicates).

Defaults to a read-only report. Deletion is always manual and explicit.

Groups where test_number differs are usually different tests from the
same book (protected by uq_book_test), not true duplicates — the report
labels them as such.

    cd backend
    venv\\Scripts\\python scripts\\cleanup_duplicate_tests.py
    venv\\Scripts\\python scripts\\cleanup_duplicate_tests.py --delete-id=<uuid>
    venv\\Scripts\\python scripts\\cleanup_duplicate_tests.py --delete-id=<uuid> --force --yes
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select

from app.core.database import async_session, engine
from app.models.attempt import Attempt
from app.models.question import Question
from app.models.section import Section
from app.models.test import Test


async def _counts(db, test_id: uuid.UUID) -> tuple[int, int]:
    attempts = (
        await db.execute(
            select(func.count()).where(Attempt.test_id == test_id)
        )
    ).scalar_one()
    questions = (
        await db.execute(
            select(func.count())
            .select_from(Question)
            .join(Section, Question.section_id == Section.id)
            .where(Section.test_id == test_id)
        )
    ).scalar_one()
    return int(attempts), int(questions)


async def report(db) -> None:
    tests = (
        await db.execute(select(Test).order_by(Test.title, Test.created_at))
    ).scalars().all()

    by_title: dict[str, list[Test]] = defaultdict(list)
    for t in tests:
        by_title[t.title].append(t)

    groups = {title: rows for title, rows in by_title.items() if len(rows) > 1}
    if not groups:
        print("No duplicate titles found.")
        return

    print(f"Found {len(groups)} title(s) shared by multiple tests:\n")
    for title, rows in sorted(groups.items()):
        numbers = {r.test_number for r in rows}
        if len(numbers) == len(rows):
            kind = "same-book tests (different test_number - NOT duplicates)"
        else:
            kind = "possible true duplicates (overlapping test_number)"

        print(f'Title "{title}" - {len(rows)} rows - {kind}')
        for r in rows:
            attempts, questions = await _counts(db, r.id)
            published = "published" if r.is_published else "draft"
            print(
                f"  id={r.id}  book_slug={r.book_slug!r}  "
                f"test_number={r.test_number}  {published}  "
                f"created_at={r.created_at.isoformat()}  "
                f"attempts={attempts}  questions={questions}"
            )
            if attempts:
                print(
                    "    WARNING: has student attempts - "
                    "do not delete without --force"
                )
        print(
            f"  Manual delete: python scripts/cleanup_duplicate_tests.py "
            f"--delete-id=<uuid>"
        )
        print()


async def delete_one(
    db,
    test_id: uuid.UUID,
    *,
    force: bool,
    yes: bool,
) -> int:
    test = await db.get(Test, test_id)
    if test is None:
        print(f"Test {test_id} not found.")
        return 1

    attempts, questions = await _counts(db, test_id)
    print(
        f'Test "{test.title}" (id={test.id}, test_number={test.test_number})\n'
        f"  attempts={attempts}  questions={questions}  "
        f"published={test.is_published}"
    )

    if attempts and not force:
        print(
            "Refusing to delete: test has attempts. "
            "Pass --force to override."
        )
        return 1

    if not yes:
        answer = input("Type DELETE to confirm: ").strip()
        if answer != "DELETE":
            print("Aborted.")
            return 1

    await db.delete(test)
    await db.commit()
    print(f"Deleted test {test_id}.")
    return 0


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--delete-id",
        help="Delete one specific test by UUID (requires confirmation).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow deleting a test that still has attempts.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the interactive confirmation (use with --delete-id).",
    )
    args = parser.parse_args()

    async with async_session() as db:
        if args.delete_id:
            try:
                test_id = uuid.UUID(args.delete_id)
            except ValueError:
                print(f"Invalid UUID: {args.delete_id}")
                await engine.dispose()
                raise SystemExit(1)
            code = await delete_one(
                db, test_id, force=args.force, yes=args.yes
            )
            await engine.dispose()
            raise SystemExit(code)

        await report(db)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
