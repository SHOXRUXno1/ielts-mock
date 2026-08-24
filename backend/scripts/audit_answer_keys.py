"""Report questions that nobody could answer correctly.

Hand every question its own answer key and see whether it earns full marks. A
question that its own key cannot satisfy cannot be satisfied by any candidate:
the mark is lost silently, the same for everyone, and nothing in the results
looks wrong until a candidate happens to pick the key and is still marked down.

Two of these have already reached candidates. One was a placeholder left in a
Listening key. The other was a whole question type: `matching` written one item
per row carried a scalar letter, while the scorer walked a dict of pairs, so
nine questions across a test had never once been marked right.

Read-only. Run it after editing a test, or against production after a deploy:

    python scripts/audit_answer_keys.py
"""

from __future__ import annotations

import asyncio
from collections import Counter
from types import SimpleNamespace

from sqlalchemy import select

from app.core.database import async_session
from app.models.question import Question
from app.models.section import Section
from app.models.test import Test
from app.services.scoring import score_answer

# Marked by a human, so there is no key to check them against.
UNMARKED = {"essay", "speaking_part"}


def ideal_answer(question: Question, qtype: str):
    """The response a candidate would give if they knew the key perfectly."""
    key = question.answer_key or {}
    correct = key.get("correct", key.get("answer"))
    content = question.content or {}

    if qtype == "multi_select":
        if isinstance(correct, list):
            return list(correct)
        return [str(correct)] if correct else None

    if qtype == "matching":
        if isinstance(correct, dict):
            return {str(k): str(v) for k, v in correct.items()}
        legacy = key.get("answers")
        if isinstance(legacy, list):
            items = content.get("items") or content.get("left") or []
            return {str(i): str(a) for i, a in zip(items, legacy)}
        return str(correct) if correct else None

    if correct is None:
        legacy = key.get("answers")
        if isinstance(legacy, list) and legacy:
            return str(legacy[0])
        return None
    if isinstance(correct, list):
        return str(correct[0]) if correct else None
    if isinstance(correct, dict):
        return correct
    return str(correct)


async def run() -> int:
    async with async_session() as session:
        questions = (await session.execute(select(Question))).scalars().all()
        sections = {
            s.id: s for s in (await session.execute(select(Section))).scalars().all()
        }
        tests = {t.id: t for t in (await session.execute(select(Test))).scalars().all()}

        checked = 0
        broken: list[tuple[Question, str, str]] = []

        for question in questions:
            qtype = str(
                getattr(question.question_type, "value", question.question_type)
            )
            if qtype in UNMARKED or question.answer_key is None:
                continue

            best = ideal_answer(question, qtype)
            if best is None:
                broken.append((question, qtype, "has no answer key to mark against"))
                continue

            probe = SimpleNamespace(
                response={"answer": best}, is_correct=None, score=None
            )
            correct, total = score_answer(question, probe)
            checked += 1
            if total == 0 or correct != total:
                broken.append(
                    (question, qtype, f"its own key scores only {correct} of {total}")
                )

        print(f"Questions checked: {checked}")
        if not broken:
            print("Every one of them can be answered correctly.")
            return 0

        print(f"Cannot be answered correctly: {len(broken)}\n")
        for question, qtype, why in broken:
            section = sections.get(question.section_id)
            test = tests.get(section.test_id) if section else None
            print(
                f"  {test.title if test else '?'}"
                f" | {section.type if section else '?'} part {section.order if section else '?'}"
                f" | question {question.order} ({qtype})"
                f" | {why}"
            )

        print()
        for qtype, count in Counter(q[1] for q in broken).most_common():
            print(f"  {count:4d}  {qtype}")
        return 1


def main() -> None:
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
