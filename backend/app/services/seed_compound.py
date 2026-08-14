"""Helpers for idempotent compound-group seeding (Listening/Reading)."""

from __future__ import annotations

import uuid
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.models.question_group import QuestionGroup


async def delete_compound_groups(
    db: AsyncSession,
    *,
    section_id: uuid.UUID,
    question_types: Iterable[str],
    title: str | None = None,
    order_range: tuple[int, int] | None = None,
) -> int:
    """Delete compound groups (questions cascade) matching the filters.

    Also removes any leftover gap rows in *order_range* that somehow lost
    their group — the failure mode that produced ghost take-UI rows.
    """
    types = {str(t) for t in question_types}
    groups = (
        await db.execute(
            select(QuestionGroup).where(QuestionGroup.section_id == section_id)
        )
    ).scalars().all()

    deleted = 0
    for g in groups:
        gtype = str(getattr(g.question_type, "value", g.question_type))
        if gtype not in types:
            continue
        if title is not None:
            shared = g.options_shared if isinstance(g.options_shared, dict) else {}
            if shared.get("title") != title:
                continue
        # Delete questions first — ORM otherwise nulls question_group_id
        # (NOT NULL since z2b3c4d5e6f7) and the flush fails.
        qs = (
            await db.execute(
                select(Question).where(Question.question_group_id == g.id)
            )
        ).scalars().all()
        for q in qs:
            await db.delete(q)
        await db.flush()
        await db.delete(g)
        deleted += 1

    if order_range is not None:
        lo, hi = order_range
        leftovers = (
            await db.execute(
                select(Question).where(
                    Question.section_id == section_id,
                    Question.order.between(lo, hi),
                    Question.question_type.in_(list(types)),
                )
            )
        ).scalars().all()
        for q in leftovers:
            await db.delete(q)
            deleted += 1

    if deleted:
        await db.flush()
    return deleted


async def next_group_order(db: AsyncSession, section_id: uuid.UUID) -> int:
    remaining = (
        await db.execute(
            select(QuestionGroup).where(QuestionGroup.section_id == section_id)
        )
    ).scalars().all()
    return max((g.order for g in remaining), default=0) + 1


def gap_answer_key(variants: list[str] | str, *, max_words: int = 1) -> dict[str, Any]:
    correct = [variants] if isinstance(variants, str) else list(variants)
    return {
        "correct": correct,
        "max_words": max_words,
        "case_sensitive": False,
    }
