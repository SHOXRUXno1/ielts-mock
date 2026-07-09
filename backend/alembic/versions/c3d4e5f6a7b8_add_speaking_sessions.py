"""Add speaking_sessions table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "speaking_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("admin_email", sa.String(length=255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("overall_band", sa.Float(), nullable=True),
        sa.Column("score_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("history_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_speaking_sessions_admin_email",
        "speaking_sessions",
        ["admin_email"],
    )


def downgrade() -> None:
    op.drop_index("ix_speaking_sessions_admin_email", table_name="speaking_sessions")
    op.drop_table("speaking_sessions")
