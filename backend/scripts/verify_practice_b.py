"""Check a Practice Set B test end to end before anyone sits it.

Same gates as verify_practice_a.py, pointed at practice-set-b.

Usage:
    cd backend
    .\\venv\\Scripts\\python scripts\\verify_practice_b.py 1
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

from app.api.tests import _collect_publish_errors  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.models.question_group import QuestionGroup  # noqa: E402
from app.models.section import Section, SectionType  # noqa: E402
from app.models.test import Test  # noqa: E402
from app.services.question_numbering import annotate_question_numbers  # noqa: E402
from app.services.storage import resolve_local_path  # noqa: E402
from seed_practice_b_common import BOOK_SLUG  # noqa: E402


def answer_summary(question) -> str:
    key = question.answer_key
    if not isinstance(key, dict):
        content = question.content if isinstance(question.content, dict) else {}
        task = content.get("task_description") or content.get("topic") or ""
        if "cue_card" in content:
            task = content["cue_card"].get("topic", "")
        if "questions" in content:
            task = f"{len(content['questions'])} prompts"
        return f"— {str(task)[:60]}"
    correct = key.get("correct")
    if isinstance(correct, list):
        return " / ".join(str(c) for c in correct)
    return str(correct)


def display_number(question) -> str:
    start = getattr(question, "computed_number", None)
    end = getattr(question, "computed_number_end", None)
    if start is None:
        return "?"
    if end and end != start:
        return f"{start}-{end}"
    return str(start)


async def report(db: AsyncSession, test_number: int) -> int:
    test = (
        await db.execute(
            select(Test)
            .options(
                selectinload(Test.sections)
                .selectinload(Section.question_groups)
                .selectinload(QuestionGroup.questions),
                selectinload(Test.sections).selectinload(Section.questions),
                selectinload(Test.section_settings),
            )
            .where(Test.book_slug == BOOK_SLUG, Test.test_number == test_number)
        )
    ).scalar_one_or_none()
    if test is None:
        print(f"test {test_number} not found — run the bootstrap script first")
        return 1

    annotate_question_numbers(test)
    print(f"{test.title}   published={test.is_published}\n")

    missing_media: list[str] = []
    for section in sorted(test.sections, key=lambda s: s.order):
        label = f"{section.type.value if isinstance(section.type, SectionType) else section.type} order={section.order}"
        header = f"-- {label}  {section.title or ''}".rstrip()
        print(header)
        if section.audio_url:
            found = resolve_local_path(section.audio_url) is not None
            print(f"     audio {section.audio_url} {'ok' if found else 'MISSING'}")
            if not found:
                missing_media.append(section.audio_url)

        for group in sorted(section.question_groups or [], key=lambda g: g.order):
            gtype = str(getattr(group.question_type, "value", group.question_type))
            print(f"   [{gtype}]")
            shared = group.options_shared if isinstance(group.options_shared, dict) else {}
            image = shared.get("image_url")
            if image:
                found = resolve_local_path(image) is not None
                print(f"     image {image} {'ok' if found else 'MISSING'}")
                if not found:
                    missing_media.append(image)
            for question in sorted(group.questions or [], key=lambda q: q.order):
                if question.image_url:
                    found = resolve_local_path(question.image_url) is not None
                    print(f"     image {question.image_url} {'ok' if found else 'MISSING'}")
                    if not found:
                        missing_media.append(question.image_url)
                print(f"     Q{display_number(question):<6} {answer_summary(question)}")
        print()

    errors = _collect_publish_errors(test)
    if errors:
        print("publish checks FAILED:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("publish checks passed")

    if missing_media:
        print(f"\n{len(missing_media)} media file(s) missing on this host:")
        for url in missing_media:
            print(f"  - {url}")

    return 1 if (errors or missing_media) else 0


async def main() -> int:
    test_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as db:
        code = await report(db, test_number)
    await engine.dispose()
    return code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
