"""Add writing_feedback table for persisting and caching live feedback.

Revision ID: v8d9e0f1a2b3
Revises: u7c8d9e0f1a2
Create Date: 2026-07-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "v8d9e0f1a2b3"
down_revision = "u7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "writing_feedback",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("attempt_id", UUID(as_uuid=True), sa.ForeignKey("attempts.id", ondelete="CASCADE"), nullable=True),
        sa.Column("task_number", sa.Integer(), nullable=False),
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("text_hash", sa.String(64), nullable=False),
        sa.Column("essay_text", sa.Text(), nullable=False),
        sa.Column("result", JSONB(), nullable=False),
        sa.Column("overall_band", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_writing_feedback_user_id", "writing_feedback", ["user_id"])
    op.create_index("ix_writing_feedback_attempt_id", "writing_feedback", ["attempt_id"])
    op.create_index("ix_writing_feedback_cache", "writing_feedback", ["prompt_hash", "text_hash"])


def downgrade() -> None:
    op.drop_table("writing_feedback")
