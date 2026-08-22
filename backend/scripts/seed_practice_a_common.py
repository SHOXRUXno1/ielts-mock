"""Shared plumbing for seeding the Practice Set A book.

The four skill scripts each own one part of a test and are safe to re-run, so
they all need the same three things: find the book's test, find one section of
it, and clear whatever a previous run left in that section.

Sections are looked up by (type, order) rather than by hard-coded UUID, so the
same scripts work against any database — local or production — without an id
list that has to be kept in step.
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

BOOK_NAME = "IELTS Practice Set A"
BOOK_SLUG = "practice-set-a"

DATA_ROOT = Path(__file__).resolve().parent / "data"


def data_dir(test_number: int) -> Path:
    return DATA_ROOT / f"practice_a_t{test_number}"


# Media lands under these names rather than the random ones the upload endpoint
# generates, so re-running a seed points at the same files instead of orphaning
# the previous copy.
AUDIO_URL = "/media/audio/practice_a_t{test}_listening_p{part}.mp3"
MAP_IMAGE_URL = "/media/images/practice_a_t{test}_listening_map.png"
CHART_IMAGE_URL = "/media/images/practice_a_t{test}_writing_task1.png"


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
            "run scripts/seed_practice_a_t1_bootstrap.py first"
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
    """Remove every group and question in a section so a re-run starts clean.

    Questions go first: the group id is NOT NULL, so letting the ORM orphan them
    fails the flush.
    """
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
    """Return (title, body) for a stored reading passage.

    The first line is the title and the rest is the passage, one paragraph per
    line, as written by scripts/_extract_booster_passages.py.
    """
    path = data_dir(test_number) / name
    if not path.exists():
        raise SystemExit(f"passage file missing: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    title = lines[0].strip()
    body = "\n".join(line for line in lines[1:] if line.strip())
    if not body:
        raise SystemExit(f"passage file has no body: {path}")
    return title, body
