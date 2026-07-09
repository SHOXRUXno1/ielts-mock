"""users v2: rename email->login, add phone/role/group_name

Revision ID: b1c2d3e4f5a6
Revises: f1a2b3c4d5e6
Create Date: 2026-07-02 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old email index before renaming
    op.drop_index("ix_users_email", table_name="users")

    # Rename email → login
    op.alter_column("users", "email", new_column_name="login")

    # Add new columns
    op.add_column("users", sa.Column("phone", sa.String(length=20), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default="student",
        ),
    )
    op.add_column("users", sa.Column("group_name", sa.String(length=100), nullable=True))

    # Create new index on login
    op.create_index(op.f("ix_users_login"), "users", ["login"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_login"), table_name="users")

    op.drop_column("users", "group_name")
    op.drop_column("users", "role")
    op.drop_column("users", "phone")

    op.alter_column("users", "login", new_column_name="email")

    op.create_index("ix_users_email", "users", ["email"], unique=True)
