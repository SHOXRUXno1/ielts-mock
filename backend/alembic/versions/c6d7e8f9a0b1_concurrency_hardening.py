"""Concurrency hardening: job retries + unique answers.

Revision ID: c6d7e8f9a0b1
Revises: b5d6e7f8a9c1
Create Date: 2026-08-11

- evaluation_jobs.retry_count for worker requeues
- unique (attempt_id, question_id) on answers (dedupe first)
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c6d7e8f9a0b1"
down_revision: Union[str, None] = "b5d6e7f8a9c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    )
    return rows.first() is not None


def _has_index(name: str) -> bool:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :n"),
        {"n": name},
    )
    return rows.first() is not None


def upgrade() -> None:
    if not _has_column("evaluation_jobs", "retry_count"):
        op.add_column(
            "evaluation_jobs",
            sa.Column(
                "retry_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )

    # Deduplicate answers before unique index (keep newest updated_at).
    op.execute(
        sa.text(
            """
            DELETE FROM answers a
            USING answers b
            WHERE a.attempt_id = b.attempt_id
              AND a.question_id = b.question_id
              AND a.id < b.id
            """
        )
    )

    if not _has_index("uq_answers_attempt_question"):
        op.create_index(
            "uq_answers_attempt_question",
            "answers",
            ["attempt_id", "question_id"],
            unique=True,
        )


def downgrade() -> None:
    if _has_index("uq_answers_attempt_question"):
        op.drop_index("uq_answers_attempt_question", table_name="answers")
    if _has_column("evaluation_jobs", "retry_count"):
        op.drop_column("evaluation_jobs", "retry_count")
