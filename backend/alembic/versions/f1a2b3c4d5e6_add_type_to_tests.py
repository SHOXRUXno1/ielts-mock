"""add type to tests

Revision ID: f1a2b3c4d5e6
Revises: ae864b45a7f5
Create Date: 2026-07-01 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "ae864b45a7f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tests",
        sa.Column(
            "type",
            sa.String(20),
            nullable=False,
            server_default="academic",
        ),
    )


def downgrade() -> None:
    op.drop_column("tests", "type")
