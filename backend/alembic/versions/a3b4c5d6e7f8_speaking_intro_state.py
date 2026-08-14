"""Add current_state and candidate_nickname for hardcoded INTRO phase.

Revision ID: a3b4c5d6e7f8
Revises: z2b3c4d5e6f7
Create Date: 2026-07-25

- Add speaking_sessions.current_state (default ended)
- Add speaking_sessions.candidate_nickname (nullable)
- Backfill in_progress sessions to part_1 (they already skipped INTRO)
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, None] = "z2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "speaking_sessions",
        sa.Column(
            "current_state",
            sa.String(length=32),
            nullable=False,
            server_default="ended",
        ),
    )
    op.add_column(
        "speaking_sessions",
        sa.Column("candidate_nickname", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_speaking_sessions_current_state",
        "speaking_sessions",
        ["current_state"],
    )
    op.execute(
        sa.text(
            "UPDATE speaking_sessions SET current_state = 'part_1' "
            "WHERE status = 'in_progress'"
        )
    )


def downgrade() -> None:
    op.drop_index(
        "ix_speaking_sessions_current_state", table_name="speaking_sessions"
    )
    op.drop_column("speaking_sessions", "candidate_nickname")
    op.drop_column("speaking_sessions", "current_state")
