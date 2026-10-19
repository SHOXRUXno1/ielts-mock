"""Seed Writing tasks from Practice Set F JSON data."""

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
from seed_practice_f_common import CHART_IMAGE_URL, clear_section, data_dir, get_section, get_test  # noqa: E402


async def main_for_test(test_number: int) -> None:
    folder = data_dir(test_number)
    path = folder / "writing.json"
    if not path.is_file():
        raise SystemExit(f"Writing data is missing: {path}")
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    task1 = data.get("task1")
    task2 = data.get("task2")
    if not isinstance(task1, dict) or not isinstance(task1.get("description"), str):
        raise SystemExit(f"Task 1 description is missing or invalid: {path}")
    if not isinstance(task2, dict) or not isinstance(task2.get("question"), str):
        raise SystemExit(f"Task 2 question is missing or invalid: {path}")

    image_path = Path(__file__).resolve().parent.parent / "media" / "images" / f"practice_f_t{test_number}_writing_task1.png"
    if not image_path.is_file():
        raise SystemExit(f"Task 1 image is required before seeding: {image_path}")

    engine = create_async_engine(settings.database_url)
    try:
        async with AsyncSession(engine, expire_on_commit=False) as db:
            test = await get_test(db, test_number)
            section = await get_section(db, test.id, SectionType.WRITING, 20)
            await clear_section(db, section.id)
            group = QuestionGroup(
                id=uuid.uuid4(), section_id=section.id, order=1,
                question_type=QuestionType.ESSAY.value, instruction="", options_shared=None,
            )
            db.add(group)
            await db.flush()
            task1_prompt = task1["description"].strip()
            task2_prompt = task2["question"].strip()
            for number, prompt, min_words, image_url in (
                (1, task1_prompt, 150, CHART_IMAGE_URL.format(test=test_number)),
                (2, task2_prompt, 250, None),
            ):
                db.add(
                    Question(
                        id=uuid.uuid4(), section_id=section.id, question_group_id=group.id,
                        order=number, question_type=QuestionType.ESSAY,
                        content={"task_description": prompt, "task_instruction": "", "prompt": prompt},
                        answer_key=None, task_number=number, min_words=min_words,
                        image_url=image_url, essay_type=None,
                    )
                )
            await db.commit()
            print(f"Done. IELTS Practice Set F Test {test_number}: 2 Writing tasks seeded.")
    finally:
        await engine.dispose()


async def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1].isdigit() or not 1 <= int(sys.argv[1]) <= 6:
        raise SystemExit("usage: python scripts/seed_practice_f_writing.py <1-6>")
    await main_for_test(int(sys.argv[1]))


if __name__ == "__main__":
    asyncio.run(main())
