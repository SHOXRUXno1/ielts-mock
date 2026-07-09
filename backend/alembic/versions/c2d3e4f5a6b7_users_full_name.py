"""users: replace first_name+last_name with full_name

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-07-03 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add full_name, populate from existing first_name + last_name, then drop them
    op.add_column(
        "users",
        sa.Column("full_name", sa.String(length=200), nullable=False, server_default=""),
    )
    # Combine existing names into full_name
    op.execute(
        "UPDATE users SET full_name = TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, ''))"
    )
    op.drop_column("users", "first_name")
    op.drop_column("users", "last_name")
    # Remove server default now that existing rows are populated
    op.alter_column("users", "full_name", server_default=None)


def downgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.String(length=100), nullable=False, server_default=""))
    op.add_column("users", sa.Column("last_name", sa.String(length=100), nullable=False, server_default=""))
    op.execute(
        "UPDATE users SET first_name = SPLIT_PART(full_name, ' ', 1), "
        "last_name = TRIM(SUBSTRING(full_name FROM POSITION(' ' IN full_name)))"
    )
    op.drop_column("users", "full_name")
