"""Add admin_sessions table for Devices page.

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-07-27
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d6e7f8a9b0c1"
down_revision: Union[str, None] = "c5d6e7f8a9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_login", sa.String(length=255), nullable=False),
        sa.Column("actor_name", sa.String(length=200), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "device_type",
            sa.String(length=16),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column("browser", sa.String(length=64), nullable=True),
        sa.Column("os_name", sa.String(length=64), nullable=True),
        sa.Column("login_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_reason", sa.String(length=16), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "ix_admin_sessions_actor_login", "admin_sessions", ["actor_login"]
    )
    op.create_index("ix_admin_sessions_user_id", "admin_sessions", ["user_id"])
    op.create_index("ix_admin_sessions_login_at", "admin_sessions", ["login_at"])
    op.create_index(
        "ix_admin_sessions_last_seen_at", "admin_sessions", ["last_seen_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_admin_sessions_last_seen_at", table_name="admin_sessions")
    op.drop_index("ix_admin_sessions_login_at", table_name="admin_sessions")
    op.drop_index("ix_admin_sessions_user_id", table_name="admin_sessions")
    op.drop_index("ix_admin_sessions_actor_login", table_name="admin_sessions")
    op.drop_table("admin_sessions")
