"""Add essay_type column and clean legacy writing content fields.

Revision ID: h4b5c6d7e8f9
Revises: g3a4b5c6d7e8
Create Date: 2026-07-09
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "h4b5c6d7e8f9"
down_revision: Union[str, None] = "g3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ESSAY_TYPES = (
    "opinion",
    "discussion",
    "problem_solution",
    "advantages_disadvantages",
    "double_question",
)


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("essay_type", sa.String(length=30), nullable=True),
    )
    op.create_check_constraint(
        "ck_questions_essay_type_values",
        "questions",
        "essay_type IS NULL OR essay_type IN ("
        + ", ".join(f"'{t}'" for t in _ESSAY_TYPES)
        + ")",
    )
    op.create_check_constraint(
        "ck_questions_essay_type_task2_only",
        "questions",
        "task_number IS DISTINCT FROM 1 OR essay_type IS NULL",
    )

    # Strip legacy content keys now that columns are source of truth
    op.execute(
        """
        UPDATE questions
        SET content = content - 'task_type' - 'min_words' - 'image_url'
        WHERE question_type = 'essay'
          AND (
            content ? 'task_type'
            OR content ? 'min_words'
            OR content ? 'image_url'
          )
        """
    )


def downgrade() -> None:
    op.drop_constraint("ck_questions_essay_type_task2_only", "questions", type_="check")
    op.drop_constraint("ck_questions_essay_type_values", "questions", type_="check")
    op.drop_column("questions", "essay_type")
    # Content cleanup is not reversed (keys were redundant with columns).
