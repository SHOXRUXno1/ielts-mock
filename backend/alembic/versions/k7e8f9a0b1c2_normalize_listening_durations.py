"""Normalize listening section durations to Part1=40, rest=0.

Revision ID: k7e8f9a0b1c2
Revises: j6d7e8f9a0b1
Create Date: 2026-07-10

DOWN is a documented no-op: prior per-row duration values are not recoverable.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "k7e8f9a0b1c2"
down_revision: Union[str, None] = "j6d7e8f9a0b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # IELTS Listening timer: 40 minutes total, stored on Part 1 only.
    op.execute(
        """
        UPDATE sections
        SET duration_minutes = 40
        WHERE type = 'listening' AND "order" = 1
        """
    )
    op.execute(
        """
        UPDATE sections
        SET duration_minutes = 0
        WHERE type = 'listening' AND "order" > 1
        """
    )


def downgrade() -> None:
    # No-op: previous per-row duration values are not recoverable after
    # normalization (some rows were 30/0/0/0, import rows were 40/40/40/40).
    pass
