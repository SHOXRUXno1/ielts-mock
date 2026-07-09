"""One-time script: normalize all answer_key fields to canonical format.

Canonical format per question type:
  mcq / true_false_ng : {"correct": "<answer string>"}
  gap_fill            : {"correct": "<answer>" | ["<a1>", "<a2>"]}  -- unchanged
  matching            : {"correct": {"<item0>": "<letter>", ...}}

Fixes produced by old seed scripts:
  - MCQ stored as {"answer": "..."} -> {"correct": "..."}
  - matching stored as {"answers": ["A","B",...]} -> {"correct": {item: letter}}

Run once:
    cd backend
    venv\\Scripts\\python scripts\\normalize_answer_keys.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.question import Question, QuestionType

DATABASE_URL = "postgresql+asyncpg://postgres:2770@localhost:5432/ielts_mock"


async def main() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(Question))
        questions: list[Question] = result.scalars().all()

        fixed = 0
        for q in questions:
            ak = q.answer_key
            content = q.content or {}
            qtype = q.question_type

            if ak is None:
                continue

            new_ak = dict(ak)
            changed = False

            # MCQ / TF-NG: {"answer": "X"} -> {"correct": "X"}
            if qtype in (QuestionType.MCQ, QuestionType.TRUE_FALSE_NG):
                if "answer" in ak and "correct" not in ak:
                    new_ak = {"correct": ak["answer"]}
                    changed = True

            # Matching: {"answers": ["A","B",...]} -> {"correct": {item: letter}}
            elif qtype in (QuestionType.MATCHING, QuestionType.MAP_LABELING):
                if "answers" in ak and "correct" not in ak:
                    items: list = content.get("items") or content.get("left") or []
                    letters: list = ak["answers"]
                    pairs = {
                        str(item): str(letter)
                        for item, letter in zip(items, letters)
                        if item
                    }
                    new_ak = {"correct": pairs}
                    changed = True
                # Also normalize {"answer": {...}} -> {"correct": {...}}
                elif "answer" in ak and isinstance(ak["answer"], dict) and "correct" not in ak:
                    new_ak = {"correct": ak["answer"]}
                    changed = True

            if changed:
                q.answer_key = new_ak
                fixed += 1
                print(f"  Fixed Q#{q.order} ({qtype}): {ak} -> {new_ak}")

        if fixed:
            await session.commit()
            print(f"\nNormalized {fixed} question(s).")
        else:
            print("All answer_key fields already canonical. Nothing to change.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
