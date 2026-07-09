"""Add writing task columns to questions

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-07-08
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "d2e3f4a5b6c7"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add nullable columns for writing-task metadata
    op.add_column("questions", sa.Column("task_number", sa.SmallInteger(), nullable=True))
    op.add_column("questions", sa.Column("min_words", sa.Integer(), nullable=True))
    op.add_column("questions", sa.Column("image_url", sa.String(500), nullable=True))

    # CHECK constraint: task_number must be 1, 2, or NULL
    op.execute(
        "ALTER TABLE questions "
        "ADD CONSTRAINT ck_questions_task_number "
        "CHECK (task_number IS NULL OR task_number IN (1, 2))"
    )

    # Backfill existing writing questions from content JSON
    op.execute("""
        UPDATE questions
        SET
            task_number = CASE
                WHEN content->>'task_type' = 'task_1' THEN 1
                WHEN content->>'task_type' = 'task_2' THEN 2
                WHEN content->>'task_number' IS NOT NULL
                    THEN (content->>'task_number')::smallint
                WHEN "order" IN (1, 2) THEN "order"
                ELSE NULL
            END,
            min_words = CASE
                WHEN content->>'min_words' IS NOT NULL
                    THEN (content->>'min_words')::int
                WHEN content->>'task_type' = 'task_1' OR "order" = 1 THEN 150
                WHEN content->>'task_type' = 'task_2' OR "order" = 2 THEN 250
                ELSE NULL
            END,
            image_url = content->>'image_url'
        WHERE question_type = 'essay'
    """)


def downgrade() -> None:
    op.execute(
        "ALTER TABLE questions "
        "DROP CONSTRAINT IF EXISTS ck_questions_task_number"
    )
    op.drop_column("questions", "image_url")
    op.drop_column("questions", "min_words")
    op.drop_column("questions", "task_number")
