"""Practice whole-section mode: practice_section_type + unique index.

Revision ID: b5d6e7f8a9c1
Revises: a4c5d6e7f8b0
Create Date: 2026-08-11

Idempotent: guarded column / index creation so partial deploys are safe.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b5d6e7f8a9c1"
down_revision: Union[str, None] = "a4c5d6e7f8b0"
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
    ).fetchall()
    return bool(rows)


def _has_index(name: str) -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :n"),
            {"n": name},
        ).fetchall()
    )


def upgrade() -> None:
    if not _has_column("attempts", "practice_section_type"):
        op.add_column(
            "attempts",
            sa.Column("practice_section_type", sa.String(length=20), nullable=True),
        )

    # Backfill from the linked Section for existing single_part attempts.
    op.execute(
        sa.text(
            """
            UPDATE attempts AS a
            SET practice_section_type = s.type
            FROM sections AS s
            WHERE a.practice_section_id = s.id
              AND a.practice_section_type IS NULL
            """
        )
    )

    if not _has_index("uq_attempt_in_progress_section"):
        op.create_index(
            "uq_attempt_in_progress_section",
            "attempts",
            ["user_id", "test_id", "practice_section_type"],
            unique=True,
            postgresql_where=sa.text(
                "status = 'in_progress' AND mode = 'single_section' "
                "AND user_id IS NOT NULL"
            ),
        )


def downgrade() -> None:
    if _has_index("uq_attempt_in_progress_section"):
        op.drop_index("uq_attempt_in_progress_section", table_name="attempts")
    if _has_column("attempts", "practice_section_type"):
        op.drop_column("attempts", "practice_section_type")
