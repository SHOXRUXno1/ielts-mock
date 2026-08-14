"""Audit listening sections that do not have exactly 10 questions.

Revision ID: l8f9a0b1c2d3
Revises: k7e8f9a0b1c2
Create Date: 2026-07-10

Warning-only: does NOT delete or modify questions. Teachers must fix
non-compliant parts manually before publish.
"""

from __future__ import annotations

import logging
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "l8f9a0b1c2d3"
down_revision: Union[str, None] = "k7e8f9a0b1c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.runtime.migration")


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        text(
            """
            SELECT s.id::text AS section_id,
                   s.test_id::text AS test_id,
                   s."order" AS part_num,
                   COUNT(q.id) AS q_count
            FROM sections s
            LEFT JOIN questions q ON q.section_id = s.id
            WHERE s.type = 'listening'
            GROUP BY s.id, s.test_id, s."order"
            HAVING COUNT(q.id) != 10
            ORDER BY s.test_id, s."order"
            """
        )
    ).fetchall()

    if not rows:
        logger.info("Listening question-count audit: all parts have exactly 10 questions.")
        return

    logger.warning(
        "Listening question-count audit: %s section(s) do not have exactly 10 questions. "
        "Publish will be blocked until fixed. Questions are NOT auto-deleted.",
        len(rows),
    )
    for row in rows:
        logger.warning(
            "  test_id=%s part=%s section_id=%s q_count=%s (expected 10)",
            row.test_id,
            row.part_num,
            row.section_id,
            row.q_count,
        )


def downgrade() -> None:
    # No-op: audit-only migration.
    pass
