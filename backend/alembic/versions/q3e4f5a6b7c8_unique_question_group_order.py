"""Add unique constraint on (question_group_id, order).

Revision ID: q3e4f5a6b7c8
Revises: p2d3e4f5a6b7
Create Date: 2026-07-12

Enforces that ``questions.order`` is unique within a group at the DB level.
Must run after p2d3e4f5a6b7 (renumber) so no duplicates remain.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "q3e4f5a6b7c8"
down_revision: Union[str, None] = "p2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Partial unique: only rows that belong to a group.
    # PostgreSQL treats NULL question_group_id as distinct, so a full unique
    # on (question_group_id, order) already allows multiple NULL-group rows
    # with the same order — which is fine (legacy path is gone).
    op.create_unique_constraint(
        "uq_question_group_order",
        "questions",
        ["question_group_id", "order"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_question_group_order", "questions", type_="unique")
