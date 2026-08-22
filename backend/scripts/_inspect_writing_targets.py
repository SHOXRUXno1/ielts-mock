"""Report which tests have both Writing tasks wired up, for load testing."""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.orm import selectinload

sys.path.insert(0, ".")

from app.core.database import async_session  # noqa: E402
from app.models.question import Question  # noqa: E402
from app.models.section import Section, SectionType  # noqa: E402
from app.models.test import Test  # noqa: E402


async def main() -> None:
    async with async_session() as db:
        tests = (
            await db.execute(
                select(Test)
                .options(selectinload(Test.sections).selectinload(Section.questions))
                .order_by(Test.created_at)
            )
        ).scalars().all()

        for t in tests:
            writing = [s for s in t.sections if s.type == SectionType.WRITING]
            qs: list[Question] = [q for s in writing for q in (s.questions or [])]
            tasks = sorted(
                (q.task_number or q.order, str(q.id), (q.content or {}).get("task_description", "")[:40])
                for q in qs
            )
            print(f"{t.id} | {t.book_name} / {t.title} | published={t.is_published}")
            print(f"   writing sections={len(writing)} questions={len(qs)}")
            for num, qid, desc in tasks:
                print(f"   task {num}: {qid}  {desc!r}")
            print()


asyncio.run(main())
