"""Drop deprecated sections.duration_minutes.

Timing lives on test_section_settings; the sections column held stale
legacy values and was ignored by the timer.

Revision ID: j3c4d5e6f7a8
Revises: i2b3c4d5e6f7
Create Date: 2026-07-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "j3c4d5e6f7a8"
down_revision: Union[str, None] = "i2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("sections", "duration_minutes")


def downgrade() -> None:
    op.add_column(
        "sections",
        sa.Column(
            "duration_minutes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
