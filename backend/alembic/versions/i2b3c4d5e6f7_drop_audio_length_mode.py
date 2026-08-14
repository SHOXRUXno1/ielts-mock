"""Migrate duration_mode audio_length → custom.

Revision ID: i2b3c4d5e6f7
Revises: h1a2b3c4d5e6
Create Date: 2026-07-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "i2b3c4d5e6f7"
down_revision: Union[str, None] = "h1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE test_section_settings "
            "SET duration_mode = 'custom' "
            "WHERE duration_mode = 'audio_length'"
        )
    )


def downgrade() -> None:
    # Irreversible — audio_length mode was removed.
    pass
