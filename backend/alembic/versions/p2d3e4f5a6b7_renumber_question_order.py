"""Renumber questions.order to be group-local 1..N.

Revision ID: p2d3e4f5a6b7
Revises: o1c2d3e4f5a6
Create Date: 2026-07-12

``questions.order`` historically mixed section-cumulative values (from Excel
import) with group-local values (from the editor). After this migration every
group's questions are numbered 1..N by their previous relative order.

Downgrade is a no-op: the original absolute orders are lossy and no longer
needed once display numbers are computed from cumulative scoring slots.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "p2d3e4f5a6b7"
down_revision: Union[str, None] = "o1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Two-step update: first shift into a high range to avoid transient
    # unique collisions within a group, then set final 1..N values.
    # (No unique constraint yet — that lands in the next migration — but
    # this pattern is safe either way.)
    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY question_group_id
                    ORDER BY "order", id
                ) AS new_order
            FROM questions
            WHERE question_group_id IS NOT NULL
        )
        UPDATE questions AS q
        SET "order" = r.new_order + 10000
        FROM ranked AS r
        WHERE q.id = r.id
          AND q."order" != r.new_order
        """
    )
    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY question_group_id
                    ORDER BY "order", id
                ) AS new_order
            FROM questions
            WHERE question_group_id IS NOT NULL
        )
        UPDATE questions AS q
        SET "order" = r.new_order
        FROM ranked AS r
        WHERE q.id = r.id
          AND q."order" != r.new_order
        """
    )


def downgrade() -> None:
    # Irreversible: original section-cumulative orders are not recoverable.
    # Display numbers no longer depend on absolute order values.
    pass
