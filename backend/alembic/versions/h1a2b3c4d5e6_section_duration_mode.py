"""Add duration_mode to test_section_settings.

Revision ID: h1a2b3c4d5e6
Revises: g9a0b1c2d3e4
Create Date: 2026-07-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "h1a2b3c4d5e6"
down_revision: Union[str, None] = "g9a0b1c2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "test_section_settings",
        sa.Column(
            "duration_mode",
            sa.String(length=20),
            server_default="standard",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("test_section_settings", "duration_mode")
