"""Safely re-mark objective sections for one completed IELTS attempt.

Use this when a scoring defect has affected a known sitting. It only updates
Listening and/or Reading; Writing and Speaking scores and evaluation jobs are
never created or changed.

Dry run:
    python scripts/rescore_objective.py <attempt-id> --section reading

Apply:
    python scripts/rescore_objective.py <attempt-id> --section reading --apply
"""

from __future__ import annotations

import argparse
import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import async_session
from app.models.answer import Answer
from app.models.attempt import Attempt, AttemptStatus
from app.models.section import Section, SectionType
from app.services.band_calc import compute_overall_band, derive_scored_status
from app.services.scoring import (
    correct_to_listening_band,
    correct_to_reading_band,
    score_section,
)


def _section_name(section_type: object) -> str:
    return str(getattr(section_type, "value", section_type))


def _target_sections(value: str) -> set[str]:
    if value == "both":
        return {SectionType.LISTENING.value, SectionType.READING.value}
    return {value}


async def run(attempt_id: uuid.UUID, target: set[str], apply: bool) -> int:
    async with async_session() as session:
        attempt = await session.get(Attempt, attempt_id)
        if attempt is None:
            print(f"Attempt {attempt_id} was not found.")
            return 1
        if attempt.status == AttemptStatus.IN_PROGRESS:
            print("Refusing to re-mark an in-progress attempt.")
            return 1

        sections = (
            await session.execute(
                select(Section)
                .options(selectinload(Section.questions))
                .where(Section.test_id == attempt.test_id)
                .where(Section.type.in_(target))
            )
        ).scalars().all()
        if not sections:
            print(f"No requested objective section exists for attempt {attempt_id}.")
            return 1

        answers = (
            await session.execute(select(Answer).where(Answer.attempt_id == attempt_id))
        ).scalars().all()
        answers_by_question = {answer.question_id: answer for answer in answers}

        changed = False
        for section in sections:
            section_name = _section_name(section.type)
            section_answers = [
                answers_by_question[question.id]
                for question in section.questions
                if question.id in answers_by_question
            ]
            if not section_answers:
                print(f"{section_name}: no submitted answers; left untouched.")
                continue

            before = {
                answer.id: (answer.is_correct, answer.score)
                for answer in section_answers
            }
            new_raw, total = score_section(section.questions, section_answers)
            answer_changed = any(
                before[answer.id] != (answer.is_correct, answer.score)
                for answer in section_answers
            )

            if section_name == SectionType.LISTENING.value:
                old_raw = attempt.listening_raw
                new_band = correct_to_listening_band(new_raw)
            else:
                old_raw = attempt.reading_raw
                new_band = correct_to_reading_band(new_raw)

            raw_changed = old_raw != new_raw
            print(
                f"{section_name}: {old_raw if old_raw is not None else 'unset'} "
                f"-> {new_raw}/{total}; band -> {new_band}"
            )
            if not raw_changed and not answer_changed:
                continue

            changed = True
            if not apply:
                continue
            if section_name == SectionType.LISTENING.value:
                attempt.listening_raw = new_raw
                attempt.listening_band = new_band
            else:
                attempt.reading_raw = new_raw
                attempt.reading_band = new_band

        if apply and changed:
            attempt.overall_band = compute_overall_band(attempt)
            attempt.status = derive_scored_status(attempt)
            await session.commit()
            print("Objective marks were updated. Writing and Speaking were not touched.")
        else:
            await session.rollback()
            print("No changes written." if not apply else "No changes were needed.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attempt_id", type=uuid.UUID)
    parser.add_argument(
        "--section",
        choices=("listening", "reading", "both"),
        default="both",
        help="Objective section to re-mark (default: both).",
    )
    parser.add_argument("--apply", action="store_true", help="Write the recalculated marks.")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.attempt_id, _target_sections(args.section), args.apply)))


if __name__ == "__main__":
    main()
