"""Link speaking_sessions to attempts/tests; rename scored → auto_scored.

Revision ID: r4f5a6b7c8d9
Revises: q3e4f5a6b7c8
Create Date: 2026-07-12

- Add nullable attempt_id / test_id FKs on speaking_sessions
- Migrate attempts.status 'scored' → 'auto_scored'
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "r4f5a6b7c8d9"
down_revision: Union[str, None] = "q3e4f5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "speaking_sessions",
        sa.Column("attempt_id", UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "speaking_sessions",
        sa.Column("test_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_speaking_sessions_attempt_id",
        "speaking_sessions",
        ["attempt_id"],
    )
    op.create_index(
        "ix_speaking_sessions_test_id",
        "speaking_sessions",
        ["test_id"],
    )
    op.create_foreign_key(
        "fk_speaking_sessions_attempt_id",
        "speaking_sessions",
        "attempts",
        ["attempt_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_speaking_sessions_test_id",
        "speaking_sessions",
        "tests",
        ["test_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute(
        sa.text("UPDATE attempts SET status = 'auto_scored' WHERE status = 'scored'")
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE attempts SET status = 'scored' "
            "WHERE status IN ('auto_scored', 'fully_scored')"
        )
    )

    op.drop_constraint(
        "fk_speaking_sessions_test_id", "speaking_sessions", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_speaking_sessions_attempt_id", "speaking_sessions", type_="foreignkey"
    )
    op.drop_index("ix_speaking_sessions_test_id", table_name="speaking_sessions")
    op.drop_index("ix_speaking_sessions_attempt_id", table_name="speaking_sessions")
    op.drop_column("speaking_sessions", "test_id")
    op.drop_column("speaking_sessions", "attempt_id")
