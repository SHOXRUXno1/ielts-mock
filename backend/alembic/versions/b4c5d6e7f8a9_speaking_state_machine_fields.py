"""Add state machine fields and remap part_1/part_3 states.

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-07-25

- Add speaking_sessions.state_entered_at
- Add speaking_sessions.current_question_index
- Backfill state_entered_at from updated_at/started_at/created_at
- Remap part_1 → part_1_active, part_3 → part_3_active
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b4c5d6e7f8a9"
down_revision: Union[str, None] = "a3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "speaking_sessions",
        sa.Column("state_entered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "speaking_sessions",
        sa.Column(
            "current_question_index",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.execute(
        sa.text(
            "UPDATE speaking_sessions "
            "SET state_entered_at = COALESCE(updated_at, started_at, created_at) "
            "WHERE state_entered_at IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE speaking_sessions "
            "SET current_state = 'part_1_active' "
            "WHERE current_state = 'part_1'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE speaking_sessions "
            "SET current_state = 'part_3_active' "
            "WHERE current_state = 'part_3'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE speaking_sessions "
            "SET current_state = 'part_1' "
            "WHERE current_state = 'part_1_active'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE speaking_sessions "
            "SET current_state = 'part_3' "
            "WHERE current_state = 'part_3_active'"
        )
    )
    op.drop_column("speaking_sessions", "current_question_index")
    op.drop_column("speaking_sessions", "state_entered_at")
