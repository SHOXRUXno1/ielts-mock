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


def _question_type_name(question_type: object) -> str:
    return str(getattr(question_type, "value", question_type))


def _canonicalize_choice_answers(section: Section, answers_by_question: dict) -> None:
    """Make legacy three-choice responses portable across scorer versions.

    Older exam pages stored ``True`` and ``Not Given`` while some deployed
    scorer versions compare these choices case-sensitively to official keys.
    Assigning a new response dict lets SQLAlchemy persist the canonical answer.
    """
    for question in section.questions:
        if _question_type_name(question.question_type) not in {
            "true_false_ng",
            "yes_no_ng",
        }:
            continue
        answer = answers_by_question.get(question.id)
        if answer is None or not isinstance(answer.response, dict):
            continue
        value = answer.response.get("answer")
        if not isinstance(value, str):
            continue
        canonical = value.strip().upper()
        if canonical != value:
            answer.response = {**answer.response, "answer": canonical}


def _score_objective_section(questions: list, answers: list) -> tuple[int, int]:
    """Score a section while repairing legacy IELTS three-choice answers.

    The normal scorer is used for every other question type.  The explicit
    branch below is intentionally independent of it: recovery must still work
    when a server is running an older, case-sensitive scorer implementation.
    """
    answers_by_question = {answer.question_id: answer for answer in answers}
    correct_total = 0
    item_total = 0

    for question in questions:
        answer = answers_by_question.get(question.id)
        question_type = _question_type_name(question.question_type)
        if question_type not in {"true_false_ng", "yes_no_ng"}:
            correct, total = score_section(
                [question], [] if answer is None else [answer]
            )
            correct_total += correct
            item_total += total
            continue

        item_total += 1
        if answer is None:
            continue
        answer_key = question.answer_key if isinstance(question.answer_key, dict) else {}
        expected = answer_key.get("correct") or answer_key.get("answer") or ""
        response = answer.response if isinstance(answer.response, dict) else {}
        submitted = response.get("answer", "")
        is_correct = str(submitted).strip().casefold() == str(expected).strip().casefold()
        answer.is_correct = is_correct
        answer.score = 1.0 if is_correct else 0.0
        correct_total += int(is_correct)

    return correct_total, item_total


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

        totals: dict[str, list[int]] = {
            section_name: [0, 0] for section_name in target
        }
        attempted: set[str] = set()
        answer_changed: dict[str, bool] = {section_name: False for section_name in target}

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
                answer.id: (answer.is_correct, answer.score, dict(answer.response or {}))
                for answer in section_answers
            }
            _canonicalize_choice_answers(section, answers_by_question)
            correct, total = _score_objective_section(section.questions, section_answers)
            answer_changed[section_name] = answer_changed[section_name] or any(
                before[answer.id]
                != (answer.is_correct, answer.score, dict(answer.response or {}))
                for answer in section_answers
            )
            totals[section_name][0] += correct
            totals[section_name][1] += total
            attempted.add(section_name)

        changed = False
        for section_name in sorted(attempted):
            new_raw, total = totals[section_name]
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
            if not raw_changed and not answer_changed[section_name]:
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
