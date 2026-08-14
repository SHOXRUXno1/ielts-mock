"""Abandon orphan in_progress speaking sessions.

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-07-25

One-time cleanup of test orphan sessions before the state machine rollout.
Sets status/current_state to abandoned and stamps finished_at.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c5d6e7f8a9b0"
down_revision: Union[str, None] = "b4c5d6e7f8a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE speaking_sessions "
            "SET status = 'abandoned', "
            "    current_state = 'abandoned', "
            "    finished_at = now() "
            "WHERE status = 'in_progress'"
        )
    )


def downgrade() -> None:
    # Test data — irreversible by design.
    pass
