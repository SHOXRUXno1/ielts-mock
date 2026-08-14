"""Practice mode: attempt.mode + practice_* columns + practice_part_settings.

Revision ID: a4c5d6e7f8b0
Revises: j3c4d5e6f7a8
Create Date: 2026-08-11

Idempotent: some environments already have ``attempts.mode`` from an earlier
partial deploy, so every DDL step uses IF NOT EXISTS / guarded checks.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a4c5d6e7f8b0"
down_revision: Union[str, None] = "j3c4d5e6f7a8"
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


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    return (
        bind.execute(
            sa.text("SELECT to_regclass(:name)"),
            {"name": f"public.{table}"},
        ).scalar()
        is not None
    )


def _has_index(name: str) -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :n"),
            {"n": name},
        ).fetchall()
    )


def _has_constraint(table: str, name: str) -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            sa.text(
                "SELECT 1 FROM information_schema.table_constraints "
                "WHERE table_name = :t AND constraint_name = :n"
            ),
            {"t": table, "n": name},
        ).fetchall()
    )


def upgrade() -> None:
    # 1) Extend attempts with mode + practice scope.
    if not _has_column("attempts", "mode"):
        op.add_column(
            "attempts",
            sa.Column(
                "mode",
                sa.String(length=16),
                nullable=False,
                server_default="full_mock",
            ),
        )
    if not _has_column("attempts", "practice_section_id"):
        op.add_column(
            "attempts",
            sa.Column(
                "practice_section_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            ),
        )
    if not _has_column("attempts", "practice_part_number"):
        op.add_column(
            "attempts",
            sa.Column("practice_part_number", sa.SmallInteger(), nullable=True),
        )
    if not _has_column("attempts", "practice_correct"):
        op.add_column(
            "attempts",
            sa.Column("practice_correct", sa.SmallInteger(), nullable=True),
        )
    if not _has_column("attempts", "practice_total"):
        op.add_column(
            "attempts",
            sa.Column("practice_total", sa.SmallInteger(), nullable=True),
        )

    if not _has_constraint("attempts", "fk_attempts_practice_section"):
        op.create_foreign_key(
            "fk_attempts_practice_section",
            "attempts",
            "sections",
            ["practice_section_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if not _has_index("ix_attempts_mode_user_test"):
        op.create_index(
            "ix_attempts_mode_user_test",
            "attempts",
            ["mode", "user_id", "test_id"],
        )

    # 2) Per-part practice settings.
    if not _has_table("practice_part_settings"):
        op.create_table(
            "practice_part_settings",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "test_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("tests.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("section_type", sa.String(length=20), nullable=False),
            sa.Column("part_number", sa.SmallInteger(), nullable=False),
            sa.Column("duration_minutes", sa.Integer(), nullable=True),
            sa.Column(
                "is_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.UniqueConstraint(
                "test_id",
                "section_type",
                "part_number",
                name="uq_practice_part_settings",
            ),
        )
    if not _has_index("ix_practice_part_settings_test_id"):
        op.create_index(
            "ix_practice_part_settings_test_id",
            "practice_part_settings",
            ["test_id"],
        )

    # 3) Partial unique indexes preserving "one in-progress per scope".
    if not _has_index("uq_attempt_in_progress_full_mock"):
        op.create_index(
            "uq_attempt_in_progress_full_mock",
            "attempts",
            ["user_id", "test_id"],
            unique=True,
            postgresql_where=sa.text(
                "status = 'in_progress' AND mode = 'full_mock' AND user_id IS NOT NULL"
            ),
        )
    if not _has_index("uq_attempt_in_progress_practice"):
        op.create_index(
            "uq_attempt_in_progress_practice",
            "attempts",
            [
                "user_id",
                "test_id",
                "practice_section_id",
                "practice_part_number",
            ],
            unique=True,
            postgresql_where=sa.text(
                "status = 'in_progress' AND mode = 'single_part' AND user_id IS NOT NULL"
            ),
        )


def downgrade() -> None:
    if _has_index("uq_attempt_in_progress_practice"):
        op.drop_index("uq_attempt_in_progress_practice", table_name="attempts")
    if _has_index("uq_attempt_in_progress_full_mock"):
        op.drop_index("uq_attempt_in_progress_full_mock", table_name="attempts")
    if _has_index("ix_practice_part_settings_test_id"):
        op.drop_index(
            "ix_practice_part_settings_test_id",
            table_name="practice_part_settings",
        )
    if _has_table("practice_part_settings"):
        op.drop_table("practice_part_settings")
    if _has_index("ix_attempts_mode_user_test"):
        op.drop_index("ix_attempts_mode_user_test", table_name="attempts")
    if _has_constraint("attempts", "fk_attempts_practice_section"):
        op.drop_constraint(
            "fk_attempts_practice_section", "attempts", type_="foreignkey"
        )
    for col in (
        "practice_total",
        "practice_correct",
        "practice_part_number",
        "practice_section_id",
        "mode",
    ):
        if _has_column("attempts", col):
            op.drop_column("attempts", col)
