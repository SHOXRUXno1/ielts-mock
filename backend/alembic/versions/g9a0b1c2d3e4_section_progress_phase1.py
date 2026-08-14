"""Section progress Phase 1: active index + backfill missing rows.

Revision ID: g9a0b1c2d3e4
Revises: f8a9b0c1d2e3
Create Date: 2026-07-27

The original section_progress migration abandoned in-progress attempts.
This revision:
- adds ix_section_progress_active (attempt_id, state)
- backfills four progress rows for attempts that still lack them
  - open statuses → NOT_STARTED
  - scored / completed statuses → SEALED with reason=submit
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g9a0b1c2d3e4"
down_revision: Union[str, None] = "f8a9b0c1d2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SECTION_TYPES = ("listening", "reading", "writing", "speaking")
_SCORED_STATUSES = {
    "completed",
    "auto_scored",
    "fully_scored",
    "completed_without_speaking",
    "partial",
}


def upgrade() -> None:
    op.create_index(
        "ix_section_progress_active",
        "section_progress",
        ["attempt_id", "state"],
    )

    conn = op.get_bind()

    # Per (attempt, section_type) gaps — covers fully-missing and partial rows.
    for section_type in _SECTION_TYPES:
        attempts = conn.execute(
            sa.text(
                """
                SELECT a.id, a.status, a.finished_at
                FROM attempts a
                WHERE NOT EXISTS (
                    SELECT 1 FROM section_progress sp
                    WHERE sp.attempt_id = a.id
                      AND sp.section_type = :section_type
                )
                """
            ),
            {"section_type": section_type},
        ).fetchall()

        for attempt_id, status, finished_at in attempts:
            if status in _SCORED_STATUSES:
                state = "sealed"
                sealed_at = finished_at
                sealed_reason = "submit"
            else:
                state = "not_started"
                sealed_at = None
                sealed_reason = None

            conn.execute(
                sa.text(
                    """
                    INSERT INTO section_progress
                        (id, attempt_id, section_type, state,
                         started_at, ends_at, sealed_at, sealed_reason,
                         created_at, updated_at)
                    VALUES
                        (gen_random_uuid(), :attempt_id, :section_type, :state,
                         NULL, NULL, :sealed_at, :sealed_reason,
                         now(), now())
                    """
                ),
                {
                    "attempt_id": attempt_id,
                    "section_type": section_type,
                    "state": state,
                    "sealed_at": sealed_at,
                    "sealed_reason": sealed_reason,
                },
            )


def downgrade() -> None:
    op.drop_index(
        "ix_section_progress_active",
        table_name="section_progress",
    )
