"""Remove duplicate choice labels in place, without reseeding any question.

Only Practice Set F Listening MCQ/multi-select option text is changed. IDs,
answers, keys, question order, attempts and publication state stay untouched.
Default is a read-only dry run; pass --apply to commit the reviewed changes.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.config import settings  # noqa: E402
from app.models.question import Question, QuestionType  # noqa: E402
from app.models.section import SectionType  # noqa: E402
from seed_practice_f_common import get_section, get_test  # noqa: E402
from seed_practice_f_listening import build_part, choice_texts  # noqa: E402


async def repair(db: AsyncSession, *, apply: bool) -> int:
    changes = []
    for test_number in range(1, 7):
        test = await get_test(db, test_number)
        for part in range(1, 5):
            section = await get_section(db, test.id, SectionType.LISTENING, part)
            _, groups = build_part(test_number, part, section.id)
            expected = {q.order: q for g in groups for q in g.questions}
            stored = (
                await db.execute(
                    select(Question)
                    .where(Question.section_id == section.id)
                    .order_by(Question.order)
                    .with_for_update()
                )
            ).scalars().all()
            if {q.order for q in stored} != set(expected):
                raise ValueError(f"Question order mismatch: T{test_number} P{part}")
            for question in stored:
                target = expected[question.order]
                if target.question_type not in {
                    QuestionType.MCQ,
                    QuestionType.MULTI_SELECT,
                }:
                    continue
                content = dict(question.content)
                content["options"] = choice_texts(content["options"])
                if (
                    question.question_type != target.question_type
                    or question.answer_key != target.answer_key
                    or content != target.content
                ):
                    raise ValueError(f"Unexpected choice data: {question.id}")
                if content != question.content:
                    changes.append((question, content))
    # Validate every candidate before assigning anything, in a single transaction.
    for question, content in changes:
        print(f"Option labels only: {question.id}")
        if apply:
            question.content = content
    if apply:
        await db.commit()
    else:
        await db.rollback()
    print(f"{'Applied' if apply else 'Dry run'}: {len(changes)} question rows")
    return len(changes)


async def main(*, apply: bool) -> None:
    engine = create_async_engine(settings.database_url)
    try:
        async with AsyncSession(engine, expire_on_commit=False) as db:
            await repair(db, apply=apply)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    asyncio.run(main(apply=parser.parse_args().apply))
