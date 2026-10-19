"""Seed Reading for any IELTS Practice Set F test from its JSON data files."""

from __future__ import annotations

import asyncio
import json
import re
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
from app.services.compound import validate_compound_structure  # noqa: E402
from app.services.seed_compound import gap_answer_key  # noqa: E402
from seed_practice_f_common import clear_section, data_dir, get_section, get_test  # noqa: E402


PASSAGE_ORDERS = (10, 11, 12)
GROUP_TYPES = {
    "classification": QuestionType.MATCHING_FEATURES,
    "matching": QuestionType.MATCHING_FEATURES,
    "matching_cause_effect": QuestionType.MATCHING_FEATURES,
    "heading_match": QuestionType.MATCHING_HEADINGS,
    "matching_paragraph": QuestionType.MATCHING_INFORMATION,
    "yes_no_not_given": QuestionType.YES_NO_NG,
    "true_false_not_given": QuestionType.TRUE_FALSE_NG,
}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"Required data file is missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"Expected a JSON object in {path}")
    return value


def _max_words(instruction: str) -> int:
    if re.search(r"ONE\s+NUMBER", instruction, re.I):
        return 1
    match = re.search(r"(?:NO MORE THAN|ONE)\s+(ONE|TWO|THREE|FOUR|\d+)\s+WORDS?", instruction, re.I)
    if not match:
        return 3
    token = match.group(1).upper()
    return {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4}.get(token, int(token) if token.isdigit() else 3)


def _gap_segments(prompt: str, gap_id: str) -> list[dict[str, str]]:
    pieces = re.split(r"___+", prompt)
    segments: list[dict[str, str]] = []
    for index, piece in enumerate(pieces):
        if piece:
            segments.append({"type": "text", "value": piece})
        if index < len(pieces) - 1:
            segments.append({"type": "gap", "gap_id": gap_id})
    if not any(segment["type"] == "gap" for segment in segments):
        raise ValueError(f"Expected a blank marker (___) in {prompt!r}")
    return segments


def _answers_for_group(
    answers: dict[str, Any], group: dict[str, Any]
) -> dict[str, str]:
    result: dict[str, str] = {}
    for number in group.get("questions", []):
        item = answers.get(str(number))
        if not isinstance(item, dict) or not isinstance(item.get("answer"), str):
            raise ValueError(f"Missing string answer for question {number}")
        result[str(number)] = item["answer"].strip()
    return result


def _options(group: dict[str, Any]) -> list[str] | None:
    raw = group.get("options", group.get("word_box", group.get("headings", group.get("list_b"))))
    if raw is None:
        return None
    if not isinstance(raw, list) or not all(isinstance(value, str) for value in raw):
        raise ValueError("Group options must be a list of strings")
    return raw


class PassageWriter:
    def __init__(self, db: AsyncSession, section_id: uuid.UUID) -> None:
        self.db = db
        self.section_id = section_id
        self.group_order = 0
        self.question_order = 0
        self.question_numbers: list[int] = []

    async def add_group(
        self,
        question_type: QuestionType,
        instruction: str,
        entries: list[tuple[int, dict[str, Any], dict[str, Any] | None]],
        options_shared: dict[str, Any] | None = None,
    ) -> None:
        if options_shared is not None and "variant" in options_shared:
            validate_compound_structure(question_type.value, options_shared)
        group = QuestionGroup(
            id=uuid.uuid4(),
            section_id=self.section_id,
            order=self.group_order + 1,
            question_type=question_type.value,
            instruction=instruction,
            options_shared=options_shared,
        )
        self.db.add(group)
        await self.db.flush()
        self.group_order += 1
        for number, content, key in entries:
            self.question_order += 1
            self.question_numbers.append(number)
            self.db.add(
                Question(
                    id=uuid.uuid4(),
                    section_id=self.section_id,
                    question_group_id=group.id,
                    order=self.question_order,
                    question_type=question_type,
                    content=content,
                    answer_key=key,
                )
            )


async def _seed_passage(
    db: AsyncSession,
    test_number: int,
    passage_index: int,
    questions_doc: dict[str, Any],
    answers_doc: dict[str, Any],
) -> list[int]:
    passage_key = f"passage_{passage_index}"
    passage_data = questions_doc.get(passage_key)
    answer_data = answers_doc.get(passage_key)
    if not isinstance(passage_data, dict) or not isinstance(answer_data, dict):
        raise ValueError(f"Missing {passage_key} in question/answer JSON")

    section = await get_section(db, (await get_test(db, test_number)).id, SectionType.READING, PASSAGE_ORDERS[passage_index - 1])
    passage_path = data_dir(test_number) / f"reading_p{passage_index}.txt"
    if not passage_path.is_file():
        raise ValueError(f"Passage text is missing: {passage_path}")
    lines = passage_path.read_text(encoding="utf-8").splitlines()
    expected_title = str(passage_data.get("title", "")).strip()
    has_title_line = bool(lines) and bool(expected_title) and lines[0].strip().casefold() == expected_title.casefold()
    source_title = expected_title or (lines[0].strip() if lines else "")
    body_lines = lines[1:] if has_title_line else lines
    passage_body = "\n".join(line for line in body_lines if line.strip())
    if not source_title or not passage_body:
        raise ValueError(f"Passage file is empty or has no body: {passage_path}")

    section.title = source_title
    section.passage = passage_body
    section.passage_subtitle = None
    writer = PassageWriter(db, section.id)
    passage_answers = answer_data.get("questions", {})
    if not isinstance(passage_answers, dict):
        raise ValueError(f"{passage_key}.questions must be an object")

    for raw_group in passage_data.get("question_groups", []):
        if not isinstance(raw_group, dict):
            raise ValueError("Question group must be an object")
        kind = str(raw_group.get("type", ""))
        instruction = str(raw_group.get("instruction", "")).strip()
        items = raw_group.get("items", {})
        numbers = raw_group.get("questions", [])
        if not instruction or not isinstance(items, dict) or not isinstance(numbers, list) or not numbers:
            raise ValueError(f"Malformed group: {raw_group!r}")
        answers = _answers_for_group(passage_answers, raw_group)
        options = _options(raw_group)
        entries: list[tuple[int, dict[str, Any], dict[str, Any] | None]] = []

        if kind in {"multiple_choice", "mcq"}:
            question_type = QuestionType.MCQ
            for number in numbers:
                item = items.get(str(number))
                if not isinstance(item, dict) or not isinstance(item.get("question"), str) or not isinstance(item.get("options"), list):
                    raise ValueError(f"Malformed MCQ item {number}")
                entries.append((number, {"question": item["question"], "options": item["options"]}, {"correct": answers[str(number)]}))
            await writer.add_group(question_type, instruction, entries)
            continue

        if kind == "multiple_choice_multi":
            question_type = QuestionType.MULTI_SELECT
            if options is None:
                raise ValueError("Multiple-select group has no options")
            answer_values = [answers[str(number)] for number in numbers]
            if len(set(answer_values)) != 1:
                raise ValueError(f"Multi-select answer keys disagree for questions {numbers}")
            correct = [value.strip() for value in answer_values[0].split(",") if value.strip()]
            if len(correct) != len(numbers):
                raise ValueError(f"Multi-select {numbers} should have {len(numbers)} correct letters")
            split = re.search(r"\bChoose\s+(?:TWO|THREE|FOUR|\d+)\b", instruction, re.I)
            prompt = instruction[: split.start()].strip() if split else instruction
            group_instruction = instruction[split.start() :].strip() if split else ""
            entries.append((numbers[0], {"question": prompt, "options": options, "choose_n": len(correct)}, {"correct": correct}))
            await writer.add_group(question_type, group_instruction, entries)
            writer.question_numbers.extend(numbers[1:])
            continue

        if kind in GROUP_TYPES:
            question_type = GROUP_TYPES[kind]
            shared_options = options
            if kind == "matching_paragraph" and shared_options is None:
                label_range = re.search(r"\b([A-F])\s*[-–]\s*([A-F])\b", instruction, re.I)
                last = label_range.group(2).upper() if label_range else "F"
                shared_options = [chr(code) for code in range(ord("A"), ord(last) + 1)]
            shared = {"options": shared_options} if shared_options is not None else None
            for number in numbers:
                prompt = items.get(str(number))
                if isinstance(prompt, dict):
                    prompt = prompt.get("question")
                if not isinstance(prompt, str):
                    raise ValueError(f"Malformed matching item {number}")
                entries.append((number, {"question": prompt}, {"correct": answers[str(number)]}))
            await writer.add_group(question_type, instruction, entries, shared)
            continue

        if kind in {"summary_completion_options", "note_completion_options", "flow_chart_completion"}:
            # Some source note tasks are matching-box questions without literal blanks.
            prompts = [items.get(str(number)) for number in numbers]
            is_compound = options is not None and all(isinstance(prompt, str) and "___" in prompt for prompt in prompts)
            if is_compound:
                question_type = {
                    "summary_completion_options": QuestionType.SUMMARY_COMPLETION,
                    "note_completion_options": QuestionType.NOTE_COMPLETION,
                    "flow_chart_completion": QuestionType.FLOW_CHART_COMPLETION,
                }[kind]
                variant = {"summary_completion_options": "summary", "note_completion_options": "notes", "flow_chart_completion": "flow"}[kind]
                segments = [_gap_segments(str(items[str(number)]), f"q{number}") for number in numbers]
                structure: dict[str, Any] = {
                    "variant": variant,
                    "instruction_words": "Choose from the word box",
                    "max_words_per_gap": 1,
                    "options": options,
                }
                if raw_group.get("title"):
                    structure["title"] = str(raw_group["title"])
                if variant == "summary":
                    structure["paragraphs"] = [{"segments": segment} for segment in segments]
                elif variant == "notes":
                    structure["sections"] = [{"heading": str(raw_group.get("title") or ""), "items": [{"segments": segment} for segment in segments]}]
                else:
                    structure["steps"] = [{"segments": segment} for segment in segments]
                for number in numbers:
                    entries.append((number, {"gap_id": f"q{number}"}, gap_answer_key([answers[str(number)]], max_words=1)))
                await writer.add_group(question_type, instruction, entries, structure)
            else:
                if options is None:
                    raise ValueError(f"{kind} group has no word box/options")
                for number in numbers:
                    prompt = items.get(str(number))
                    if not isinstance(prompt, str):
                        raise ValueError(f"Malformed option-matching item {number}")
                    entries.append((number, {"question": prompt}, {"correct": answers[str(number)]}))
                await writer.add_group(QuestionType.MATCHING_FEATURES, instruction, entries, {"options": options})
            continue

        if kind in {"completion", "short_answer"}:
            for number in numbers:
                prompt = items.get(str(number))
                if not isinstance(prompt, str):
                    raise ValueError(f"Malformed short-answer item {number}")
                if options is not None:
                    entries.append((number, {"question": prompt}, {"correct": answers[str(number)]}))
                else:
                    max_words = _max_words(instruction)
                    entries.append((number, {"prompt": prompt, "question": prompt, "max_words": max_words}, {"correct": answers[str(number)], "max_words": max_words, "case_sensitive": False}))
            await writer.add_group(QuestionType.MATCHING_FEATURES if options is not None else QuestionType.SHORT_ANSWER, instruction, entries, {"options": options} if options is not None else None)
            continue

        raise ValueError(f"Unsupported question group type {kind!r} in {passage_key}")

    return writer.question_numbers


async def seed(db: AsyncSession, test_number: int) -> None:
    test = await get_test(db, test_number)
    folder = data_dir(test_number)
    questions_doc = _read_json(folder / "reading_questions.json")
    answers_doc = _read_json(folder / "reading_answers.json")

    # Validate every passage before clearing any existing data.
    for passage_index in range(1, 4):
        key = f"passage_{passage_index}"
        passage_data = questions_doc.get(key)
        answer_data = answers_doc.get(key)
        if not isinstance(passage_data, dict) or not isinstance(answer_data, dict):
            raise SystemExit(f"Missing {key} in reading question/answer data")
        expected = [number for group in passage_data.get("question_groups", []) for number in group.get("questions", [])]
        actual = sorted(int(number) for number in answer_data.get("questions", {}).keys())
        if sorted(expected) != actual:
            raise SystemExit(f"Question/key mismatch in {key}: questions={sorted(expected)} keys={actual}")

    sections = [await get_section(db, test.id, SectionType.READING, order) for order in PASSAGE_ORDERS]
    for section in sections:
        await clear_section(db, section.id)
    all_numbers: list[int] = []
    for passage_index, section in enumerate(sections, start=1):
        numbers = await _seed_passage(db, test_number, passage_index, questions_doc, answers_doc)
        all_numbers.extend(numbers)
        print(f"Passage {passage_index}: {len(numbers)} questions seeded")
    if len(all_numbers) != 40 or sorted(all_numbers) != list(range(1, 41)):
        raise SystemExit(f"Expected Reading questions 1-40 exactly once; got {sorted(all_numbers)}")
    await db.commit()
    print(f"Done. IELTS Practice Set F Test {test_number}: 40 Reading questions seeded.")


async def main_for_test(test_number: int) -> None:
    engine = create_async_engine(settings.database_url)
    try:
        async with AsyncSession(engine, expire_on_commit=False) as db:
            await seed(db, test_number)
    finally:
        await engine.dispose()


async def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1].isdigit() or not 1 <= int(sys.argv[1]) <= 6:
        raise SystemExit("usage: python scripts/seed_practice_f_reading.py <1-6>")
    await main_for_test(int(sys.argv[1]))


if __name__ == "__main__":
    asyncio.run(main())
