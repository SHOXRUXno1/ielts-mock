"""Single-part practice: unit enumeration, duration resolution, settings CRUD.

Design notes
------------
* A "practice unit" is one addressable part inside a test — Listening Part 2,
  Reading Passage 3, Writing Task 1, Speaking Part 2. For Writing the unit is
  the essay task (task_number), so one Writing ``Section`` yields two units.
* Duration lives in ``practice_part_settings`` per (test, section_type,
  part_number). Missing rows fall back to a **proportional** default derived
  from ``TestSectionSettings`` (Listening 30 min / 4 parts = 7.5 min each,
  Reading 60 min / 3 passages = 20 min each, Writing 60 min for T2 vs T1, etc.).
* Speaking practice units are AI-paced — the safety cap in section_progress
  applies exactly as it does for the full mock.
"""

from __future__ import annotations

import logging
import math
import uuid
from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.practice_part_settings import PracticePartSettings
from app.models.section import Section, SectionType
from app.models.test_section_settings import TestSectionSettings
from app.services import section_settings as settings_service
from app.services.scoring import scoring_slots_for_question

logger = logging.getLogger(__name__)

# Writing is scored per-task, but Task 2 traditionally consumes ~2/3 of the
# 60 minute Writing budget. Practice defaults follow the same split.
WRITING_TASK_MINUTES: dict[int, int] = {1: 20, 2: 40}
WRITING_TASK_DEFAULT = 20
# How long each speaking part typically runs (used only as a UI hint; the
# state machine keeps its own hard cap).
SPEAKING_PART_MINUTES: dict[int, int] = {1: 5, 2: 4, 3: 5}


@dataclass(frozen=True)
class PracticeUnit:
    section_type: str
    part_number: int
    section_id: uuid.UUID
    label: str
    question_count: int
    duration_minutes: int | None
    duration_is_default: bool
    is_enabled: bool


@dataclass(frozen=True)
class PracticeSectionUnit:
    """A whole-skill practice unit (e.g. Full Listening = all 4 parts)."""

    section_type: str
    label: str
    part_count: int
    question_count: int
    duration_minutes: int | None
    is_enabled: bool


_SECTION_LABELS: dict[str, str] = {
    SectionType.LISTENING.value: "Full Listening",
    SectionType.READING.value: "Full Reading",
    SectionType.WRITING.value: "Full Writing",
    SectionType.SPEAKING.value: "Full Speaking",
}


def _stype(section: Section) -> str:
    return section.type.value if hasattr(section.type, "value") else str(section.type)


def _writing_task_number(question) -> int | None:
    task = getattr(question, "task_number", None)
    if task in (1, 2):
        return task
    order = getattr(question, "order", None)
    return order if order in (1, 2) else None


def _writing_units(section: Section) -> list[tuple[int, list[object]]]:
    """Group writing essays into ``[(task_number, [questions])]`` ordered 1,2."""
    by_task: dict[int, list[object]] = {}
    for q in section.questions or []:
        qtype = getattr(q, "question_type", None)
        qtype_value = getattr(qtype, "value", qtype)
        if qtype_value != "essay":
            continue
        task = _writing_task_number(q)
        if task is None:
            continue
        by_task.setdefault(task, []).append(q)
    return [(task, by_task[task]) for task in sorted(by_task)]


def _scoring_slots(questions: Sequence[object]) -> int:
    return sum(scoring_slots_for_question(q) for q in questions)


def default_duration(
    section_type: str,
    part_number: int,
    section_duration_minutes: int | None,
    part_count: int,
) -> int | None:
    """Proportional default for a part in a section.

    * ``listening`` / ``reading``: total minutes split evenly across parts,
      rounded to the nearest minute (never below 1).
    * ``writing``: Task 1 = 20 min, Task 2 = 40 min (fixed IELTS convention).
    * ``speaking``: AI-paced (returns None).
    """
    if section_type == SectionType.SPEAKING.value:
        return None
    if section_type == SectionType.WRITING.value:
        return WRITING_TASK_MINUTES.get(part_number, WRITING_TASK_DEFAULT)
    if section_duration_minutes is None or part_count <= 0:
        return None
    per_part = section_duration_minutes / part_count
    return max(1, int(round(per_part)))


async def enumerate_units(
    db: AsyncSession,
    test_id: uuid.UUID,
) -> list[PracticeUnit]:
    """List every part of a test as a practice unit.

    Enforces the canonical order Listening → Reading → Writing → Speaking, and
    within each type the section ``order`` (or task_number for Writing).
    """
    sections_result = await db.execute(
        select(Section).where(Section.test_id == test_id)
    )
    sections = sorted(sections_result.scalars().all(), key=lambda s: s.order)
    if not sections:
        return []

    for section in sections:
        # Eager-load questions for scoring-slot counts and writing task grouping.
        await db.refresh(section, attribute_names=["questions"])

    section_settings = await settings_service.ensure_settings(db, test_id)
    section_minutes = {row.section_type: row.duration_minutes for row in section_settings}

    part_settings = await load_settings(db, test_id)
    settings_by_key = {(r.section_type, r.part_number): r for r in part_settings}

    grouped: dict[str, list[Section]] = {}
    for section in sections:
        grouped.setdefault(_stype(section), []).append(section)

    ordered_types = [t.value for t in SectionType if t.value in grouped]
    units: list[PracticeUnit] = []
    for stype in ordered_types:
        skill_sections = grouped[stype]
        if stype == SectionType.WRITING.value:
            # One Writing Section — surface every essay task as a separate unit.
            writing_section = skill_sections[0]
            tasks = _writing_units(writing_section)
            part_count = max(len(tasks), 1)
            for task_number, qs in tasks:
                settings_row = settings_by_key.get((stype, task_number))
                custom = settings_row.duration_minutes if settings_row else None
                default = default_duration(stype, task_number, section_minutes.get(stype), part_count)
                units.append(
                    PracticeUnit(
                        section_type=stype,
                        part_number=task_number,
                        section_id=writing_section.id,
                        label=f"Task {task_number}",
                        question_count=len(qs),
                        duration_minutes=custom if custom is not None else default,
                        duration_is_default=custom is None,
                        is_enabled=settings_row.is_enabled if settings_row else True,
                    )
                )
            continue

        part_count = len(skill_sections)
        for idx, section in enumerate(skill_sections, start=1):
            settings_row = settings_by_key.get((stype, idx))
            custom = settings_row.duration_minutes if settings_row else None
            default = default_duration(stype, idx, section_minutes.get(stype), part_count)
            label = _label_for(stype, idx)
            slots = _scoring_slots(section.questions or [])
            units.append(
                PracticeUnit(
                    section_type=stype,
                    part_number=idx,
                    section_id=section.id,
                    label=label,
                    question_count=slots,
                    duration_minutes=custom if custom is not None else default,
                    duration_is_default=custom is None,
                    is_enabled=settings_row.is_enabled if settings_row else True,
                )
            )
    return units


def _label_for(section_type: str, part_number: int) -> str:
    if section_type == SectionType.LISTENING.value:
        return f"Part {part_number}"
    if section_type == SectionType.READING.value:
        return f"Passage {part_number}"
    if section_type == SectionType.SPEAKING.value:
        return f"Part {part_number}"
    return f"Part {part_number}"


async def load_settings(
    db: AsyncSession,
    test_id: uuid.UUID,
) -> list[PracticePartSettings]:
    result = await db.execute(
        select(PracticePartSettings).where(
            PracticePartSettings.test_id == test_id
        )
    )
    return list(result.scalars().all())


async def find_unit(
    db: AsyncSession,
    test_id: uuid.UUID,
    section_type: str,
    part_number: int,
) -> PracticeUnit | None:
    for unit in await enumerate_units(db, test_id):
        if unit.section_type == section_type and unit.part_number == part_number:
            return unit
    return None


async def enumerate_section_units(
    db: AsyncSession,
    test_id: uuid.UUID,
) -> list[PracticeSectionUnit]:
    """List whole-skill practice units for a test (one per present section type)."""
    sections_result = await db.execute(
        select(Section).where(Section.test_id == test_id)
    )
    sections = sorted(sections_result.scalars().all(), key=lambda s: s.order)
    if not sections:
        return []

    for section in sections:
        await db.refresh(section, attribute_names=["questions"])

    section_settings = await settings_service.ensure_settings(db, test_id)
    section_minutes = {row.section_type: row.duration_minutes for row in section_settings}

    grouped: dict[str, list[Section]] = {}
    for section in sections:
        grouped.setdefault(_stype(section), []).append(section)

    units: list[PracticeSectionUnit] = []
    for stype in (t.value for t in SectionType if t.value in grouped):
        skill_sections = grouped[stype]
        if stype == SectionType.WRITING.value:
            writing_section = skill_sections[0]
            tasks = _writing_units(writing_section)
            part_count = max(len(tasks), 1)
            # Writing tasks count as essays, not scoring slots.
            question_count = sum(len(qs) for _, qs in tasks) if tasks else 0
        elif stype == SectionType.SPEAKING.value:
            part_count = len(skill_sections)
            question_count = part_count
        else:
            part_count = len(skill_sections)
            question_count = sum(
                _scoring_slots(s.questions or []) for s in skill_sections
            )

        duration = section_minutes.get(stype)
        if stype == SectionType.SPEAKING.value:
            duration = None  # AI-paced; safety cap applies at enter time

        units.append(
            PracticeSectionUnit(
                section_type=stype,
                label=_SECTION_LABELS.get(stype, f"Full {stype.title()}"),
                part_count=part_count,
                question_count=question_count,
                duration_minutes=duration,
                is_enabled=True,
            )
        )
    return units


async def find_section_unit(
    db: AsyncSession,
    test_id: uuid.UUID,
    section_type: str,
) -> PracticeSectionUnit | None:
    for unit in await enumerate_section_units(db, test_id):
        if unit.section_type == section_type:
            return unit
    return None


async def upsert_setting(
    db: AsyncSession,
    test_id: uuid.UUID,
    section_type: str,
    part_number: int,
    *,
    duration_minutes: int | None,
    is_enabled: bool,
) -> PracticePartSettings:
    """Create or update the per-part row. ``duration_minutes=None`` reverts to
    the proportional default."""
    result = await db.execute(
        select(PracticePartSettings).where(
            PracticePartSettings.test_id == test_id,
            PracticePartSettings.section_type == section_type,
            PracticePartSettings.part_number == part_number,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = PracticePartSettings(
            test_id=test_id,
            section_type=section_type,
            part_number=part_number,
            duration_minutes=duration_minutes,
            is_enabled=is_enabled,
        )
        db.add(row)
    else:
        row.duration_minutes = duration_minutes
        row.is_enabled = is_enabled
    await db.flush()
    return row


def duration_for_practice_attempt(
    unit: PracticeUnit,
) -> int | None:
    """Duration to enforce for a practice attempt of this unit.

    None for AI-paced speaking; positive minutes otherwise.
    """
    if unit.section_type == SectionType.SPEAKING.value:
        return unit.duration_minutes  # usually None; caller applies safety cap
    return unit.duration_minutes


def _proportional_from_settings(
    section_settings: Sequence[TestSectionSettings],
    section_type: str,
    part_number: int,
    part_count: int,
) -> int | None:
    """Compute a duration without loading questions (fast path)."""
    section_minutes = None
    for row in section_settings:
        if row.section_type == section_type:
            section_minutes = row.duration_minutes
            break
    return default_duration(section_type, part_number, section_minutes, part_count)


async def resolve_duration_minutes(
    db: AsyncSession,
    test_id: uuid.UUID,
    section_type: str,
    part_number: int,
    *,
    part_count: int,
) -> int | None:
    """Fast lookup used by section_progress.compute_ends_at for practice attempts."""
    result = await db.execute(
        select(PracticePartSettings.duration_minutes).where(
            PracticePartSettings.test_id == test_id,
            PracticePartSettings.section_type == section_type,
            PracticePartSettings.part_number == part_number,
        )
    )
    row = result.first()
    if row is not None and row[0] is not None:
        return int(row[0])
    section_settings = await settings_service.ensure_settings(db, test_id)
    return _proportional_from_settings(section_settings, section_type, part_number, part_count)
