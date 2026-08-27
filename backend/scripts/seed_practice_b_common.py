"""Shared plumbing for seeding Practice Set B (Longman Practice Tests Plus 2).

Student-facing name stays anonymous. The source book is only named in comments
and in this module, so a leaked title does not show up in the catalogue.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.models.question_group import QuestionGroup
from app.models.section import Section, SectionType
from app.models.test import Test

BOOK_NAME = "IELTS Practice Set B"
BOOK_SLUG = "practice-set-b"
SOURCE_BOOK = "IELTS Practice Tests Plus 2"

DATA_ROOT = Path(__file__).resolve().parent / "data"
MEDIA_AUDIO = Path(__file__).resolve().parent.parent / "media" / "audio"
MEDIA_IMAGES = Path(__file__).resolve().parent.parent / "media" / "images"

PLUS2_ROOT = Path(r"C:\Users\brawl\Desktop\Ielts boosters\IELTS Practice Tests Plus 2")
PLUS2_PDF = PLUS2_ROOT / "IELTS Practice Tests Plus 2.pdf"
PLUS2_AUDIO = PLUS2_ROOT / "IELTS Practice Tests Plus 2 Audio"


def data_dir(test_number: int) -> Path:
    return DATA_ROOT / f"practice_b_t{test_number}"


AUDIO_URL = "/media/audio/practice_b_t{test}_listening_p{part}.mp3"
MAP_IMAGE_URL = "/media/images/practice_b_t{test}_listening_map.png"
CHART_IMAGE_URL = "/media/images/practice_b_t{test}_writing_task1.png"


async def get_test(db: AsyncSession, test_number: int) -> Test:
    test = (
        await db.execute(
            select(Test).where(
                Test.book_slug == BOOK_SLUG, Test.test_number == test_number
            )
        )
    ).scalar_one_or_none()
    if test is None:
        raise SystemExit(
            f"{BOOK_NAME} test {test_number} not found — "
            "run scripts/seed_practice_b_bootstrap.py first"
        )
    return test


async def get_section(
    db: AsyncSession, test_id: uuid.UUID, section_type: SectionType, order: int
) -> Section:
    section = (
        await db.execute(
            select(Section).where(
                Section.test_id == test_id,
                Section.type == section_type,
                Section.order == order,
            )
        )
    ).scalar_one_or_none()
    if section is None:
        raise SystemExit(f"{section_type.value} section order={order} not found")
    return section


async def clear_section(db: AsyncSession, section_id: uuid.UUID) -> int:
    removed = 0
    groups = (
        await db.execute(
            select(QuestionGroup).where(QuestionGroup.section_id == section_id)
        )
    ).scalars().all()
    for group in groups:
        questions = (
            await db.execute(
                select(Question).where(Question.question_group_id == group.id)
            )
        ).scalars().all()
        for question in questions:
            await db.delete(question)
            removed += 1
        await db.flush()
        await db.delete(group)

    strays = (
        await db.execute(select(Question).where(Question.section_id == section_id))
    ).scalars().all()
    for question in strays:
        await db.delete(question)
        removed += 1

    if removed or groups:
        await db.flush()
    return removed


def read_passage(test_number: int, name: str) -> tuple[str, str]:
    path = data_dir(test_number) / name
    if not path.exists():
        raise SystemExit(f"passage file missing: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    title = lines[0].strip()
    body = "\n".join(line for line in lines[1:] if line.strip())
    if not body:
        raise SystemExit(f"passage file has no body: {path}")
    return title, body
