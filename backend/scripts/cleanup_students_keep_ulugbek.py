"""Remove student data while preserving one verified student profile.

Default mode is a read-only preflight.  Deletion requires ``--apply`` and is
performed in one transaction, after the protected profile has been verified.

Run inside the backend container:
    python scripts/cleanup_students_keep_ulugbek.py
    python scripts/cleanup_students_keep_ulugbek.py --apply
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence

from sqlalchemy import delete, func, or_, select

sys.path.insert(0, ".")

from app.core.database import async_session  # noqa: E402
from app.models.answer import Answer  # noqa: E402
from app.models.attempt import Attempt  # noqa: E402
from app.models.evaluation_job import EvaluationJob  # noqa: E402
from app.models.question import Question  # noqa: E402
from app.models.section import Section  # noqa: E402
from app.models.section_progress import SectionProgress  # noqa: E402
from app.models.speaking_session import SpeakingSession  # noqa: E402
from app.models.test import Test  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.writing_feedback import WritingFeedback  # noqa: E402


KEEP_FULL_NAME = "Ulug'bek Baxodirov"
STUDENT_ROLE = "student"


async def _count(db, model, *conditions) -> int:
    return int((await db.scalar(select(func.count()).select_from(model).where(*conditions))) or 0)


async def _ids(db, statement) -> list:
    return list((await db.execute(statement)).scalars().all())


def _format_counts(title: str, counts: dict[str, int]) -> None:
    print(f"\n{title}")
    for label, value in counts.items():
        print(f"  {label}: {value}")


async def _load_target(db) -> User:
    matches = list(
        (
            await db.execute(
                select(User).where(
                    User.role == STUDENT_ROLE,
                    User.full_name == KEEP_FULL_NAME,
                )
            )
        )
        .scalars()
        .all()
    )
    if len(matches) != 1:
        raise RuntimeError(
            f"Safety stop: expected exactly one student named {KEEP_FULL_NAME!r}; "
            f"found {len(matches)}. No changes were made."
        )
    return matches[0]


async def _snapshot(db, target: User) -> tuple[dict[str, int], list, list]:
    student_ids = await _ids(
        db,
        select(User.id).where(User.role == STUDENT_ROLE),
    )
    attempt_ids = await _ids(
        db,
        select(Attempt.id).where(Attempt.user_id.in_(student_ids)),
    )
    removable_user_ids = [student_id for student_id in student_ids if student_id != target.id]

    feedback_scope = or_(
        WritingFeedback.user_id.in_(student_ids),
        WritingFeedback.attempt_id.in_(attempt_ids),
    )
    counts = {
        "students kept": 1,
        "students to delete": len(removable_user_ids),
        "student attempts to delete": len(attempt_ids),
        "answers to delete": await _count(db, Answer, Answer.attempt_id.in_(attempt_ids)),
        "evaluation jobs to delete": await _count(
            db, EvaluationJob, EvaluationJob.attempt_id.in_(attempt_ids)
        ),
        "section progress rows to delete": await _count(
            db, SectionProgress, SectionProgress.attempt_id.in_(attempt_ids)
        ),
        "speaking sessions to delete": await _count(
            db, SpeakingSession, SpeakingSession.attempt_id.in_(attempt_ids)
        ),
        "writing feedback rows to delete": await _count(db, WritingFeedback, feedback_scope),
        "tests protected": await _count(db, Test),
        "sections protected": await _count(db, Section),
        "questions protected": await _count(db, Question),
    }
    return counts, student_ids, attempt_ids


async def _verify_after(db, target_id, protected_counts: dict[str, int]) -> None:
    current_counts = {
        "tests protected": await _count(db, Test),
        "sections protected": await _count(db, Section),
        "questions protected": await _count(db, Question),
    }
    if current_counts != protected_counts:
        raise RuntimeError(
            "Safety stop: protected test-content counts changed unexpectedly. "
            "Transaction was rolled back."
        )

    students_left = await _count(db, User, User.role == STUDENT_ROLE)
    target_attempts = await _count(db, Attempt, Attempt.user_id == target_id)
    target_feedback = await _count(db, WritingFeedback, WritingFeedback.user_id == target_id)
    if students_left != 1 or target_attempts != 0 or target_feedback != 0:
        raise RuntimeError(
            "Safety stop: post-cleanup verification failed. Transaction was rolled back."
        )

    print("\nVerification passed")
    print(f"  students remaining: {students_left}")
    print(f"  attempts for {KEEP_FULL_NAME}: {target_attempts}")
    print(f"  writing feedback for {KEEP_FULL_NAME}: {target_feedback}")
    _format_counts("Protected content unchanged", current_counts)


async def _apply(
    db,
    target_id,
    student_ids: Sequence,
    attempt_ids: Sequence,
    protected_counts: dict[str, int],
) -> None:
    removable_user_ids = [student_id for student_id in student_ids if student_id != target_id]
    feedback_scope = or_(
        WritingFeedback.user_id.in_(student_ids),
        WritingFeedback.attempt_id.in_(attempt_ids),
    )

    # The read-only preflight opens SQLAlchemy's implicit transaction. Close it
    # before beginning the explicit all-or-nothing deletion transaction.
    await db.rollback()
    async with db.begin():
        # Speaking sessions use SET NULL on attempt deletion, so remove these
        # explicitly instead of leaving unlinked recordings/history behind.
        await db.execute(delete(SpeakingSession).where(SpeakingSession.attempt_id.in_(attempt_ids)))
        await db.execute(delete(WritingFeedback).where(feedback_scope))
        await db.execute(delete(Answer).where(Answer.attempt_id.in_(attempt_ids)))
        await db.execute(delete(EvaluationJob).where(EvaluationJob.attempt_id.in_(attempt_ids)))
        await db.execute(delete(SectionProgress).where(SectionProgress.attempt_id.in_(attempt_ids)))
        await db.execute(delete(Attempt).where(Attempt.id.in_(attempt_ids)))
        await db.execute(delete(User).where(User.id.in_(removable_user_ids)))
        await _verify_after(db, target_id, protected_counts)


async def main(apply: bool) -> None:
    async with async_session() as db:
        target = await _load_target(db)
        target_id = target.id
        counts, student_ids, attempt_ids = await _snapshot(db, target)
        print("Protected student")
        print(f"  id: {target.id}")
        print(f"  full name: {target.full_name}")
        print(f"  login: {target.login}")
        _format_counts("Preflight (no changes made)", counts)

        if not apply:
            print("\nDry run complete. Re-run with --apply to delete the listed student data.")
            return

        await _apply(
            db,
            target_id,
            student_ids,
            attempt_ids,
            {key: counts[key] for key in ("tests protected", "sections protected", "questions protected")},
        )
        print("\nCleanup completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete the preflighted student data. Omit for a read-only dry run.",
    )
    args = parser.parse_args()
    asyncio.run(main(args.apply))
