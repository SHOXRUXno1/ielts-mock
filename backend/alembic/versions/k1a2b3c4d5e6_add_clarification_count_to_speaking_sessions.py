"""Add clarification_count to speaking_sessions.

Revision ID: k1a2b3c4d5e6
Revises: i0d1e2f3a4b5
Create Date: 2026-10-09

Tracks consecutive clarification requests ("Pardon?", "Could you repeat?")
on the current question. Reset to 0 whenever the question index or state
advances. See app.services.speaking_clarification.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "k1a2b3c4d5e6"
down_revision: Union[str, None] = "i0d1e2f3a4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default so existing rows get 0 at the DB level without a
    # follow-up UPDATE and without needing a nullable intermediate state.
    op.add_column(
        "speaking_sessions",
        sa.Column(
            "clarification_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("speaking_sessions", "clarification_count")
