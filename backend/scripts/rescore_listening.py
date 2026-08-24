"""Re-mark Listening for sittings of a test whose answer key has been corrected.

A key is occasionally wrong when a sitting is graded — a placeholder left in by
whoever built the test, a missing spelling variant. Fixing the key does not
disturb marks already awarded, so candidates keep the score the old key gave
them until somebody re-marks the paper. This does that.

Only Listening is recomputed. The re-score endpoint also re-queues Writing and
Speaking for the AI examiner, which would move bands that have nothing to do
with the key that was fixed, so it is deliberately not used here.

Nothing is written unless --apply is passed, and only sittings whose raw score
actually moves are touched.

Dry run:  python scripts/rescore_listening.py "Cambridge IELTS 9"
Apply:    python scripts/rescore_listening.py --apply "Cambridge IELTS 9"
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import async_session
from app.models.answer import Answer
from app.models.attempt import Attempt, AttemptStatus
from app.models.section import Section, SectionType
from app.models.test import Test
from app.models.user import User
from app.services.band_calc import compute_overall_band, derive_scored_status
from app.services.scoring import correct_to_listening_band, score_section


def describe(value: object) -> str:
    if value is None or value == "":
        return "(nothing)"
    return repr(value)


async def run(title_fragment: str, apply: bool) -> int:
    async with async_session() as session:
        tests = (
            await session.execute(
                select(Test).where(Test.title.ilike(f"%{title_fragment}%"))
            )
        ).scalars().all()
        if not tests:
            print(f"No test matches {title_fragment!r}.")
            return 1
        for test in tests:
            print(f"Test: {test.title}")

        test_ids = [t.id for t in tests]

        sections = (
            await session.execute(
                select(Section)
                .options(selectinload(Section.questions))
                .where(Section.test_id.in_(test_ids))
                .where(Section.type == SectionType.LISTENING)
            )
        ).scalars().all()
        questions_by_test: dict[object, list] = {}
        for section in sections:
            questions_by_test.setdefault(section.test_id, []).extend(section.questions)

        attempts = (
            await session.execute(
                select(Attempt)
                .where(Attempt.test_id.in_(test_ids))
                .where(Attempt.status != AttemptStatus.IN_PROGRESS)
                .order_by(Attempt.created_at)
            )
        ).scalars().all()
        print(f"Sittings to check: {len(attempts)}\n")

        changed = 0
        never_scored: list[str] = []
        for attempt in attempts:
            questions = questions_by_test.get(attempt.test_id, [])
            if not questions:
                continue
            question_ids = {q.id for q in questions}

            answers = [
                a
                for a in (
                    await session.execute(
                        select(Answer).where(Answer.attempt_id == attempt.id)
                    )
                ).scalars().all()
                if a.question_id in question_ids
            ]
            if not answers:
                continue

            was_correct = {a.question_id: a.is_correct for a in answers}
            new_raw, _total = score_section(questions, answers)
            old_raw = attempt.listening_raw

            if old_raw is None:
                # Never carried a Listening score at all, so the key that was
                # fixed is not what is wrong with it. Worth knowing about,
                # not worth quietly grading here.
                never_scored.append(f"attempt={attempt.id} status={attempt.status}")
                continue

            if old_raw == new_raw:
                continue

            student = await session.get(User, attempt.user_id) if attempt.user_id else None
            name = getattr(student, "full_name", None) or "(unknown candidate)"
            new_band = correct_to_listening_band(new_raw)
            print(f"{name}: listening {old_raw} -> {new_raw} raw, band {attempt.listening_band} -> {new_band}")

            by_id = {q.id: q for q in questions}
            for answer in answers:
                if answer.is_correct == was_correct[answer.question_id]:
                    continue
                question = by_id[answer.question_id]
                verdict = "now correct" if answer.is_correct else "now wrong"
                typed = (answer.response or {}).get("answer")
                print(f"    question {question.order}: {verdict}, wrote {describe(typed)}")

            if apply:
                attempt.listening_raw = new_raw
                attempt.listening_band = new_band
                attempt.overall_band = compute_overall_band(attempt)
                attempt.status = derive_scored_status(attempt)
            changed += 1

        if apply and changed:
            await session.commit()
            print(f"\nRe-marked {changed} sitting(s).")
        elif changed:
            await session.rollback()
            print(f"\n{changed} sitting(s) would change. Re-run with --apply to write them.")
        else:
            await session.rollback()
            print("No sitting changes.")

        if never_scored:
            print(
                f"\nLeft alone: {len(never_scored)} sitting(s) that never carried a "
                "Listening score. Something else went wrong with those."
            )
            for line in never_scored:
                print(f"    {line}")
    return 0


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--apply"]
    apply = "--apply" in sys.argv[1:]
    if len(args) != 1:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(asyncio.run(run(args[0], apply)))


if __name__ == "__main__":
    main()
