"""Add subtitle to question_groups.

Revision ID: o1c2d3e4f5a6
Revises: n0b1c2d3e4f5
Create Date: 2026-07-11

Optional context heading shown to students between the group instruction
and the question list (e.g. "Loneliness and mental health" for MCQ blocks).
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "o1c2d3e4f5a6"
down_revision: Union[str, None] = "n0b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "question_groups",
        sa.Column("subtitle", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("question_groups", "subtitle")
