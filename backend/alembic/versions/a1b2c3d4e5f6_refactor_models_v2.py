"""refactor models v2: question answer_key, attempt nullable user + timestamps, evaluation_job section-based

Revision ID: a1b2c3d4e5f6
Revises: 69de1e7301e5
Create Date: 2026-06-13 13:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "69de1e7301e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- questions: rename correct_answer -> answer_key --
    op.alter_column("questions", "correct_answer", new_column_name="answer_key")

    # -- attempts: user_id nullable + new timestamp columns + allow 'scored' status --
    op.alter_column("attempts", "user_id", existing_type=sa.UUID(), nullable=True)
    op.add_column("attempts", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("attempts", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))

    # -- evaluation_jobs: drop answer_id FK + old columns, add new columns --
    op.drop_index(op.f("ix_evaluation_jobs_status"), table_name="evaluation_jobs")
    op.drop_constraint("evaluation_jobs_answer_id_key", "evaluation_jobs", type_="unique")
    op.drop_constraint("evaluation_jobs_answer_id_fkey", "evaluation_jobs", type_="foreignkey")
    op.drop_column("evaluation_jobs", "answer_id")
    op.drop_column("evaluation_jobs", "feedback")

    op.add_column("evaluation_jobs", sa.Column("section_type", sa.String(length=20), nullable=False, server_default="writing"))
    op.add_column("evaluation_jobs", sa.Column("input_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"))
    op.add_column("evaluation_jobs", sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("evaluation_jobs", sa.Column("teacher_override_band", sa.Float(), nullable=True))
    op.add_column("evaluation_jobs", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))

    # Remove server defaults that were only needed for the migration
    op.alter_column("evaluation_jobs", "section_type", server_default=None)
    op.alter_column("evaluation_jobs", "input_data", server_default=None)

    op.create_index(op.f("ix_evaluation_jobs_status"), "evaluation_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_evaluation_jobs_status"), table_name="evaluation_jobs")

    op.drop_column("evaluation_jobs", "processed_at")
    op.drop_column("evaluation_jobs", "teacher_override_band")
    op.drop_column("evaluation_jobs", "result")
    op.drop_column("evaluation_jobs", "input_data")
    op.drop_column("evaluation_jobs", "section_type")

    op.add_column("evaluation_jobs", sa.Column("answer_id", sa.UUID(), nullable=False))
    op.add_column("evaluation_jobs", sa.Column("feedback", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_foreign_key("evaluation_jobs_answer_id_fkey", "evaluation_jobs", "answers", ["answer_id"], ["id"], ondelete="CASCADE")
    op.create_unique_constraint("evaluation_jobs_answer_id_key", "evaluation_jobs", ["answer_id"])

    op.create_index(op.f("ix_evaluation_jobs_status"), "evaluation_jobs", ["status"], unique=False)

    op.drop_column("attempts", "finished_at")
    op.drop_column("attempts", "started_at")
    op.alter_column("attempts", "user_id", existing_type=sa.UUID(), nullable=False)

    op.alter_column("questions", "answer_key", new_column_name="correct_answer")
