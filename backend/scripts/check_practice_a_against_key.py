"""Compare a seeded Practice Set A test against the publisher's answer sheet.

The scoring check proves the platform marks what was seeded; it cannot tell that
what was seeded is what the book says. This reads the printed key straight from
the PDF and lines it up with the database, question by question.

The printed conventions are expanded before comparing:
  "Students'/Student Union"  -> either spelling
  "(About) 10"               -> with or without the bracketed part
  "(Fully) insures"          -> likewise
A row passes when any accepted variant in the database matches any reading of
the printed answer. Rows that do not match are printed for a human to judge:
a wider set of accepted spellings is usually right, a different answer is not.

Runs against the local database only, since it needs the source PDFs.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\check_practice_a_against_key.py 5
"""

from __future__ import annotations

import asyncio
import itertools
import re
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _parse_booster_answers import parse as parse_key  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.models.question_group import QuestionGroup  # noqa: E402
from app.models.section import Section, SectionType  # noqa: E402
from app.models.test import Test  # noqa: E402
from app.services.question_numbering import annotate_question_numbers  # noqa: E402
from seed_practice_a_common import BOOK_SLUG  # noqa: E402

PAREN_RE = re.compile(r"\(([^)]*)\)")
FOOTNOTE_MARKS = "*˚°"


def normalise(value: str) -> str:
    text = value.strip().lower().strip(FOOTNOTE_MARKS)
    text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    text = re.sub(r"[.,;:!?\"]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_bled_letters(cell: str) -> str:
    """Drop letters that belong to a neighbouring "any order" block.

    Those letters always carry the footnote mark that means "in any order", so a
    marked single letter trailing a worded answer came from the block below, not
    from this row.
    """
    return re.sub(rf"(?:\s+\b[A-J]\b[{FOOTNOTE_MARKS}])+\s*$", "", cell).strip()


def readings(printed: str) -> set[str]:
    """Every answer the printed cell allows.

    Slashes separate alternatives and brackets mark an optional part, so a cell
    like "(About) 10/ten" stands for four acceptable answers.
    """
    cell = printed.strip().strip(FOOTNOTE_MARKS)
    out: set[str] = set()

    for alternative in re.split(r"\s*/\s*", cell):
        alternative = alternative.strip()
        if not alternative:
            continue
        brackets = PAREN_RE.findall(alternative)
        # Try each combination of keeping or dropping the bracketed parts.
        for keep in itertools.product([True, False], repeat=len(brackets)):
            text = alternative
            for inner, keep_it in zip(brackets, keep):
                text = text.replace(f"({inner})", inner if keep_it else "", 1)
            out.add(normalise(text))

    # A cell of the form "a/b c" also reads as "a c" — the trailing words belong
    # to both alternatives.
    parts = re.split(r"\s*/\s*", cell)
    if len(parts) > 1 and " " in parts[-1]:
        tail = parts[-1].split(" ", 1)[1]
        for part in parts[:-1]:
            out.add(normalise(f"{part} {tail}"))

    return {value for value in out if value}


def seeded_variants(question) -> list[str]:
    key = question.answer_key if isinstance(question.answer_key, dict) else {}
    correct = key.get("correct")
    if correct is None:
        return []
    if isinstance(correct, list):
        return [str(v) for v in correct]
    return [str(correct)]


async def compare(db: AsyncSession, test_number: int) -> int:
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

    problems = 0
    for skill, section_type in (
        ("listening", SectionType.LISTENING),
        ("reading", SectionType.READING),
    ):
        printed = parse_key(skill).get(test_number, {})
        if not printed:
            print(f"── {skill}: no printed key found, skipping")
            continue

        by_number: dict[int, list[str]] = {}
        multi_select_ranges: list[tuple[int, int]] = []
        for section in test.sections:
            if section.type != section_type:
                continue
            for group in section.question_groups or []:
                questions = list(group.questions or [])
                numbers: list[int] = []
                for question in questions:
                    start = getattr(question, "computed_number", None)
                    end = getattr(question, "computed_number_end", None) or start
                    if start is None:
                        continue
                    numbers.extend(range(start, end + 1))

                # "These answers in any order" prints its letters down the column
                # in an order the candidate is not asked to reproduce, and marking
                # ignores it too, so the whole group is compared as one pool.
                if str(group.question_type) == "multi_select" and numbers:
                    pool = [v for q in questions for v in seeded_variants(q)]
                    for number in numbers:
                        by_number.setdefault(number, []).extend(pool)
                    multi_select_ranges.append((min(numbers), max(numbers)))
                    continue

                for question in questions:
                    start = getattr(question, "computed_number", None)
                    end = getattr(question, "computed_number_end", None) or start
                    if start is None:
                        continue
                    for number in range(start, end + 1):
                        by_number.setdefault(number, []).extend(
                            seeded_variants(question)
                        )

        mismatches: list[str] = []
        checked = 0
        handled: set[int] = set()

        # The answer sheet prints an "any order" block as a bare column of
        # letters whose lines do not sit level with the numbered rows, so the
        # letters land on neighbouring numbers when the sheet is read. Compare
        # such a block as a set drawn from its own rows plus the row above.
        for start, end in multi_select_ranges:
            window = [printed.get(n, "") for n in range(max(1, start - 1), end + 1)]
            pool = {
                letter.upper()
                for cell in window
                for letter in re.findall(r"\b([A-J])\b", cell.upper())
            }
            seeded = {v.strip().upper() for v in by_number.get(start, [])}
            checked += end - start + 1
            handled.update(range(start, end + 1))
            if not seeded or not seeded <= pool:
                mismatches.append(
                    f"Q{start}-{end}: book offers {sorted(pool)}, seeded {sorted(seeded)}"
                )

        for number in range(1, 41):
            if number in handled:
                continue
            cell = printed.get(number)
            variants = by_number.get(number)
            if not cell or not variants:
                mismatches.append(f"Q{number}: missing ({'key' if not cell else 'seed'})")
                continue
            checked += 1
            allowed = readings(strip_bled_letters(cell))
            seeded = {normalise(v) for v in variants}
            # A grouped answer ("in any order") prints one letter per row but the
            # rows share display numbers, so a hit anywhere in the group counts.
            if not (seeded & allowed):
                mismatches.append(
                    f"Q{number}: book says {cell!r}, seeded {sorted(seeded)}"
                )

        print(f"── {skill}: {checked} compared, {len(mismatches)} to look at")
        for line in mismatches:
            print(f"     {line}")
        problems += len(mismatches)

    print("\nMATCHES THE BOOK" if not problems else f"\n{problems} row(s) need a look")
    return 1 if problems else 0


async def main() -> int:
    test_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        code = await compare(db, test_number)
    await engine.dispose()
    return code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
