"""Sit a Practice Set E test three times in memory and check the marking.

Same gates as check_practice_a_scoring.py, pointed at practice-set-e.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\check_practice_e_scoring.py 1
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.models.answer import Answer  # noqa: E402
from app.models.question import Question  # noqa: E402
from app.models.question_group import QuestionGroup  # noqa: E402
from app.models.section import Section, SectionType  # noqa: E402
from app.models.test import Test  # noqa: E402
from app.services.question_numbering import annotate_question_numbers  # noqa: E402
from app.services.scoring import (  # noqa: E402
    correct_to_listening_band,
    correct_to_reading_band,
    score_answer,
    scoring_slots_for_question,
)
from seed_practice_e_common import BOOK_SLUG  # noqa: E402

MULTI = "multi_select"


def canonical(question: Question) -> object:
    key = question.answer_key or {}
    correct = key.get("correct")
    if question.question_type == MULTI:
        return [correct] if not isinstance(correct, list) else correct
    if isinstance(correct, list):
        return correct[0]
    return correct


def messy(value: object) -> object:
    if isinstance(value, list):
        return [f"  {str(v).lower()} " for v in value]
    return f"  {str(value).lower()} "


def build_answer(question: Question, value: object) -> Answer:
    return Answer(question_id=question.id, response={"answer": value})


def run_candidate(questions: list[Question], transform) -> tuple[int, int, list[str]]:
    got = 0
    total = 0
    misses: list[str] = []
    for question in questions:
        value = transform(question)
        answer = build_answer(question, value)
        correct, slots = score_answer(question, answer)
        got += correct
        total += slots
        if correct < slots:
            number = getattr(question, "computed_number", "?")
            end = getattr(question, "computed_number_end", None)
            label = f"Q{number}-{end}" if end else f"Q{number}"
            misses.append(
                f"{label} [{question.question_type}] "
                f"sent={value!r} key={(question.answer_key or {}).get('correct')!r} "
                f"({correct}/{slots})"
            )
    return got, total, misses


def variant_check(questions: list[Question]) -> list[str]:
    rejected: list[str] = []
    for question in questions:
        key = question.answer_key or {}
        correct = key.get("correct")
        if question.question_type == MULTI or not isinstance(correct, list):
            continue
        number = getattr(question, "computed_number", "?")
        for variant in correct:
            answer = build_answer(question, variant)
            got, slots = score_answer(question, answer)
            if got < slots:
                limit = key.get("max_words")
                rejected.append(
                    f"Q{number} {variant!r} scored {got}/{slots} "
                    f"(words={len(str(variant).split())}, max_words={limit})"
                )
    return rejected


async def check(db: AsyncSession, test_number: int) -> int:
    test = (
        await db.execute(
            select(Test)
            .options(
                selectinload(Test.sections)
                .selectinload(Section.question_groups)
                .selectinload(QuestionGroup.questions),
                selectinload(Test.sections).selectinload(Section.questions),
            )
            .where(Test.book_slug == BOOK_SLUG, Test.test_number == test_number)
        )
    ).scalar_one_or_none()
    if test is None:
        print(f"test {test_number} not found")
        return 1

    annotate_question_numbers(test)
    print(f"{test.title}\n")

    failures = 0
    for section_type, to_band in (
        (SectionType.LISTENING, correct_to_listening_band),
        (SectionType.READING, correct_to_reading_band),
    ):
        questions = [
            q
            for s in sorted(test.sections, key=lambda s: s.order)
            if s.type == section_type
            for g in sorted(s.question_groups or [], key=lambda g: g.order)
            for q in sorted(g.questions or [], key=lambda q: q.order)
        ]
        slots = sum(scoring_slots_for_question(q) for q in questions)
        name = section_type.value.capitalize()
        print(f"-- {name}: {len(questions)} rows, {slots} marks")

        perfect, total, misses = run_candidate(questions, canonical)
        print(f"   perfect   {perfect}/{total}  band {to_band(perfect)}")
        for miss in misses:
            print(f"      MISMARKED {miss}")
        if perfect != total or total != 40:
            failures += 1

        soft, total, misses = run_candidate(questions, lambda q: messy(canonical(q)))
        print(f"   messy     {soft}/{total}  band {to_band(soft)}")
        for miss in misses:
            print(f"      REJECTED {miss}")
        if soft != total:
            failures += 1

        zero, total, _ = run_candidate(questions, lambda q: "qqzzxx")
        print(f"   clueless  {zero}/{total}  band {to_band(zero)}")
        if zero != 0:
            failures += 1

        rejected = variant_check(questions)
        if rejected:
            failures += 1
            print(f"   variants  {len(rejected)} accepted answer(s) NOT credited:")
            for line in rejected:
                print(f"      {line}")
        else:
            print("   variants  every accepted answer credited")
        print()

    writing = [
        q
        for s in test.sections
        if s.type == SectionType.WRITING
        for g in s.question_groups or []
        for q in g.questions or []
    ]
    speaking = [
        q
        for s in test.sections
        if s.type == SectionType.SPEAKING
        for g in s.question_groups or []
        for q in g.questions or []
    ]
    print(f"-- Writing: {len(writing)} task(s), Speaking: {len(speaking)} part(s) "
          "— graded by the model, no keys to check")

    print("\nMARKING OK" if failures == 0 else f"\n{failures} MARKING PROBLEM(S)")
    return 1 if failures else 0


async def main() -> int:
    test_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        code = await check(db, test_number)
    await engine.dispose()
    return code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
