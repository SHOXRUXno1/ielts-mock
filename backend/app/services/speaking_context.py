"""Build examiner context string from a test's authored speaking sections.

Thin wrapper around speaking_plan for the legacy session-less Gemini path.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.section import Section
from app.services.speaking_plan import (
    format_plan_as_context,
    load_speaking_plan,
    plan_from_sections,
)


def format_speaking_context_from_sections(speaking_sections: list[Section]) -> str | None:
    """Format PART 1/2/3 examiner context from ordered speaking sections.

    Returns None when no usable authored content is present (caller should
    fall back to the hardcoded generic examiner prompt).
    """
    plan = plan_from_sections(speaking_sections)
    return format_plan_as_context(plan)


async def build_speaking_context(
    test_id: uuid.UUID,
    db: AsyncSession,
) -> str | None:
    """Load speaking sections for a test and format examiner context."""
    plan = await load_speaking_plan(test_id, db)
    return format_plan_as_context(plan)
