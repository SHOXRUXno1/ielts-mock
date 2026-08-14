"""Add test_section_settings table; move duration to section-type level.

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-07-27
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f8a9b0c1d2e3"
down_revision: Union[str, None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "test_section_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "test_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section_type", sa.String(length=20), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
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
            name="uq_test_section_settings",
        ),
    )
    op.create_index(
        "ix_test_section_settings_test_id",
        "test_section_settings",
        ["test_id"],
    )

    # Backfill preserving today's behaviour: duration was SUM over part rows.
    # Speaking stays untimed (AI-paced).
    op.execute(
        sa.text(
            """
            INSERT INTO test_section_settings
                (id, test_id, section_type, duration_minutes, created_at, updated_at)
            SELECT gen_random_uuid(), s.test_id, s.type,
                   CASE WHEN s.type = 'speaking' THEN NULL
                        ELSE NULLIF(SUM(s.duration_minutes), 0) END,
                   now(), now()
            FROM sections s
            GROUP BY s.test_id, s.type
            """
        )
    )


def downgrade() -> None:
    op.drop_index(
        "ix_test_section_settings_test_id",
        table_name="test_section_settings",
    )
    op.drop_table("test_section_settings")
