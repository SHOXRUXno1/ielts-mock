"""Add passage_subtitle to sections.

Revision ID: u7c8d9e0f1a2
Revises: t6b7c8d9e0f1
Create Date: 2026-07-15
"""

from alembic import op
import sqlalchemy as sa

revision = "u7c8d9e0f1a2"
down_revision = "t6b7c8d9e0f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sections", sa.Column("passage_subtitle", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("sections", "passage_subtitle")
