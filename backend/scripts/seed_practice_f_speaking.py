"""Seed Speaking Parts 1-3 from Practice Set F JSON data."""

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
from seed_practice_f_common import clear_section, data_dir, get_section, get_test  # noqa: E402


async def main_for_test(test_number: int) -> None:
    path = data_dir(test_number) / "speaking.json"
    if not path.is_file():
        raise SystemExit(f"Speaking data is missing: {path}")
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    expected_parts = ("part1", "part2", "part3")
    if any(not isinstance(data.get(part), dict) for part in expected_parts):
        raise SystemExit(f"Speaking data must contain part1, part2 and part3: {path}")

    plan: list[tuple[int, str, dict[str, Any]]] = []
    for order, part_key in zip((30, 31, 32), expected_parts, strict=True):
        part = data[part_key]
        if part_key == "part2":
            if not isinstance(part.get("prompt"), str) or not isinstance(part.get("bullet_points"), list):
                raise SystemExit("Part 2 needs a prompt and bullet_points list")
            content = {
                "part": 2,
                "cue_card": {
                    "topic": str(part.get("topic", "")),
                    "bullets": part["bullet_points"],
                },
            }
        else:
            if not isinstance(part.get("questions"), list) or not all(isinstance(q, str) for q in part["questions"]):
                raise SystemExit(f"{part_key} needs a questions list")
            content = {
                "part": 1 if part_key == "part1" else 3,
                "topic": str(part.get("topic", "")),
                "questions": part["questions"],
            }
            if part_key == "part3":
                content["topics"] = [str(part.get("topic", ""))]
        label = str(part.get("topic", "")).strip()
        plan.append((order, part_key, {"content": content, "label": label}))

    sections_doc = data_dir(test_number) / "sections.json"
    titles = json.loads(sections_doc.read_text(encoding="utf-8")).get("titles", {}) if sections_doc.is_file() else {}
    engine = create_async_engine(settings.database_url)
    try:
        async with AsyncSession(engine, expire_on_commit=False) as db:
            test = await get_test(db, test_number)
            for order, part_key, item in plan:
                section = await get_section(db, test.id, SectionType.SPEAKING, order)
                await clear_section(db, section.id)
                section.title = titles.get(f"speaking:{order}") or f"Part {order - 29} — {item['label']}"
                group = QuestionGroup(
                    id=uuid.uuid4(), section_id=section.id, order=1,
                    question_type=QuestionType.SPEAKING_PART.value, instruction="", options_shared=None,
                )
                db.add(group)
                await db.flush()
                db.add(
                    Question(
                        id=uuid.uuid4(), section_id=section.id, question_group_id=group.id,
                        order=1, question_type=QuestionType.SPEAKING_PART,
                        content=item["content"], answer_key=None,
                    )
                )
                print(f"Part {order - 29}: {item['label']}")
            await db.commit()
            print(f"Done. IELTS Practice Set F Test {test_number}: Speaking Parts 1-3 seeded.")
    finally:
        await engine.dispose()


async def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1].isdigit() or not 1 <= int(sys.argv[1]) <= 6:
        raise SystemExit("usage: python scripts/seed_practice_f_speaking.py <1-6>")
    await main_for_test(int(sys.argv[1]))


if __name__ == "__main__":
    asyncio.run(main())
