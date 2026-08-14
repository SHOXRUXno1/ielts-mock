"""DB helpers for per-test section settings (duration source of truth)."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.section import SectionType
from app.models.test_section_settings import TestSectionSettings
from app.services.section_duration import DURATION_RULES, recommended_for

logger = logging.getLogger(__name__)

TYPE_ORDER: tuple[str, ...] = tuple(DURATION_RULES.keys())


def _order_key(section_type: str) -> int:
    try:
        return TYPE_ORDER.index(section_type)
    except ValueError:
        return len(TYPE_ORDER)


def build_default_rows(test_id: uuid.UUID) -> list[TestSectionSettings]:
    """Unsaved settings rows with recommended durations for every section type."""
    return [
        TestSectionSettings(
            test_id=test_id,
            section_type=stype,
            duration_minutes=recommended_for(stype),
            duration_mode="standard",
        )
        for stype in TYPE_ORDER
    ]


async def load_settings(
    db: AsyncSession,
    test_id: uuid.UUID,
) -> list[TestSectionSettings]:
    result = await db.execute(
        select(TestSectionSettings).where(TestSectionSettings.test_id == test_id)
    )
    rows = list(result.scalars().all())
    rows.sort(key=lambda r: _order_key(r.section_type))
    return rows


def _log_missing(test_id: uuid.UUID, missing: list[TestSectionSettings]) -> None:
    for row in missing:
        logger.warning(
            "Missing TestSectionSettings for test=%s section=%s. "
            "Auto-creating with default.",
            test_id,
            row.section_type,
        )


async def ensure_settings(
    db: AsyncSession,
    test_id: uuid.UUID,
) -> list[TestSectionSettings]:
    """Load settings, creating missing rows with recommended durations."""
    rows = await load_settings(db, test_id)
    existing = {r.section_type for r in rows}
    missing = [r for r in build_default_rows(test_id) if r.section_type not in existing]
    if missing:
        _log_missing(test_id, missing)
        db.add_all(missing)
        await db.flush()
        rows = [*rows, *missing]
        rows.sort(key=lambda r: _order_key(r.section_type))
    return rows


async def ensure_loaded(db: AsyncSession, test) -> None:
    """Fill in missing settings on a Test whose relationship is already loaded.

    Older tests predate test_section_settings; they get recommended defaults
    the first time anyone reads them.
    """
    existing = {s.section_type for s in test.section_settings}
    missing = [r for r in build_default_rows(test.id) if r.section_type not in existing]
    if not missing:
        return
    _log_missing(test.id, missing)
    test.section_settings.extend(missing)
    await db.commit()


def durations_map(rows: list[TestSectionSettings]) -> dict[str, int | None]:
    return {r.section_type: r.duration_minutes for r in rows}


def timed_total_minutes(rows: list[TestSectionSettings]) -> int:
    """Sum of timed-section durations (catalog / intro estimates; speaking excluded)."""
    return sum(
        r.duration_minutes or 0
        for r in rows
        if r.section_type != SectionType.SPEAKING.value
    )
