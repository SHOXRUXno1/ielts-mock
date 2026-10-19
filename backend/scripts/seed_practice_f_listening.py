"""Seed all four Listening parts from the reviewed Practice Set F JSON files.

Each multi-select task is one row with N scoring slots, so choice order does
not affect marking. Every compound gap remains a separate question row.
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.models.question import Question, QuestionType  # noqa: E402
from app.models.question_group import QuestionGroup  # noqa: E402
from app.models.section import SectionType  # noqa: E402
from app.services.compound import (  # noqa: E402
    extract_gap_ids,
    is_compound_type,
    validate_compound_structure,
)
from app.services.scoring import scoring_slots_for_question  # noqa: E402
from app.services.seed_compound import gap_answer_key  # noqa: E402
from seed_practice_f_common import (  # noqa: E402
    clear_section,
    data_dir,
    get_section,
    get_test,
)


def read_document(test_number: int, name: str) -> dict[str, Any]:
    path = data_dir(test_number) / name
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def option_letters(options: list[str]) -> set[str]:
    return {option.split(".", maxsplit=1)[0].strip() for option in options}


def build_part(
    test_number: int,
    part_number: int,
    section_id: uuid.UUID,
) -> tuple[str, list[QuestionGroup]]:
    """Compile and validate a complete part before touching stored questions."""
    key = f"part_{part_number}"
    part = read_document(test_number, "listening_questions.json")[key]
    answers = read_document(test_number, "listening_answers.json")[key]["questions"]
    expected = list(range((part_number - 1) * 10 + 1, part_number * 10 + 1))
    numbers = [n for group in part["question_groups"] for n in group["questions"]]
    if numbers != expected or sorted(map(int, answers)) != expected:
        raise ValueError(f"Test {test_number} {key}: question/key coverage mismatch")

    result = []
    question_order = 0
    for group_order, raw in enumerate(part["question_groups"], start=1):
        kind = QuestionType(raw["type"])
        numbers = raw["questions"]
        instruction = raw["instruction"].strip()
        shared = raw.get("options_shared")
        if not instruction:
            raise ValueError(f"Missing instruction: Test {test_number} Q{numbers[0]}")
        compound = is_compound_type(kind)
        if compound:
            validate_compound_structure(kind, shared)
            if set(extract_gap_ids(shared)) != {f"q{n}" for n in numbers}:
                raise ValueError(f"Gap/key mismatch: Test {test_number} Q{numbers[0]}")

        group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=section_id,
            order=group_order,
            question_type=kind.value,
            instruction=instruction,
            options_shared=shared,
            questions=[],
        )
        item_numbers = [numbers[0]] if kind is QuestionType.MULTI_SELECT else numbers
        if set(raw["items"]) != {str(n) for n in item_numbers}:
            raise ValueError(f"Unexpected items: Test {test_number} Q{numbers[0]}")
        for number in item_numbers:
            content = dict(raw["items"][str(number)])
            correct = answers[str(number)]["correct"]
            if kind is QuestionType.MULTI_SELECT:
                correct = [answers[str(n)]["correct"] for n in numbers]
                if len(set(correct)) != len(numbers):
                    raise ValueError(f"Duplicate multi-select keys: Q{number}")
                if content.get("choose_n") != len(numbers):
                    raise ValueError(f"Wrong multi-select slot count: Q{number}")
                if not set(correct) <= option_letters(content["options"]):
                    raise ValueError(f"Multi-select key outside options: Q{number}")
                answer_key = {"correct": correct}
            elif compound or kind is QuestionType.SHORT_ANSWER:
                words = shared["max_words_per_gap"] if compound else raw["max_words"]
                if not compound:
                    content["max_words"] = words
                if not isinstance(correct, list) or not correct or not all(correct):
                    raise ValueError(f"Missing text answer variants: Q{number}")
                answer_key = gap_answer_key(correct, max_words=words)
            else:
                options = content.get("options") or (shared or {}).get("options")
                if not options or correct not in option_letters(options):
                    raise ValueError(f"Key outside options: Q{number}")
                answer_key = {"correct": correct}
            question_order += 1
            group.questions.append(
                Question(
                    id=uuid.uuid4(),
                    section_id=section_id,
                    question_group_id=group.id,
                    order=question_order,
                    question_type=kind,
                    content=content,
                    answer_key=answer_key,
                )
            )
        result.append(group)
    total = sum(scoring_slots_for_question(q) for g in result for q in g.questions)
    if total != 10:
        raise ValueError(f"Test {test_number} {key}: expected 10 marks, got {total}")
    return part["title"], result


async def seed(db: AsyncSession, test_number: int) -> None:
    test = await get_test(db, test_number)
    sections = [
        await get_section(db, test.id, SectionType.LISTENING, part)
        for part in range(1, 5)
    ]
    plans = [
        build_part(test_number, part, section.id)
        for part, section in enumerate(sections, start=1)
    ]
    for part, (section, (title, groups)) in enumerate(zip(sections, plans), start=1):
        await clear_section(db, section.id)
        section.title = f"Part {part} — {title}"
        db.add_all(groups)
        print(f"Part {part}: {len(groups)} groups, 10 marks")
    await db.commit()
    print(f"Done. IELTS Practice Set F Test {test_number}: 40 Listening marks seeded.")


async def main_for_test(test_number: int) -> None:
    engine = create_async_engine(settings.database_url)
    try:
        async with AsyncSession(engine, expire_on_commit=False) as db:
            await seed(db, test_number)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].isdigit() or not 1 <= int(sys.argv[1]) <= 6:
        raise SystemExit("usage: python scripts/seed_practice_f_listening.py <1-6>")
    asyncio.run(main_for_test(int(sys.argv[1])))
