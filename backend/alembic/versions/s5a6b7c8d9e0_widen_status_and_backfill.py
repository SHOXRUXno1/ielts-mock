"""Widen attempts.status to String(32) and backfill data integrity fixes.

Revision ID: s5a6b7c8d9e0
Revises: r4f5a6b7c8d9
Create Date: 2026-07-13

1. Widen status column String(20) → String(32) for new enum values.
2. Abandon stale in_progress attempts (updated_at > 24h ago).
3. Abandon empty completed attempts (all bands NULL, updated_at > 1h ago).
4. writing_band = 0.0 → NULL (legacy Task-2-missing sentinel).
5. Stuck auto_scored + speaking_session in_progress (>1h) →
   attempt completed_without_speaking, session abandoned.
"""

from datetime import datetime, timedelta, timezone

from alembic import op
import sqlalchemy as sa

revision = "s5a6b7c8d9e0"
down_revision = "r4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "attempts", "status",
        type_=sa.String(32),
        existing_type=sa.String(20),
    )

    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    # 1. Abandon stale in_progress (inactive >24h)
    r1 = conn.execute(
        sa.text(
            "UPDATE attempts SET status = 'abandoned' "
            "WHERE status = 'in_progress' AND updated_at < :cutoff"
        ),
        {"cutoff": now - timedelta(hours=24)},
    )

    # 2. Abandon empty completed (all bands NULL, >1h — avoids in-flight evals)
    r2 = conn.execute(
        sa.text(
            "UPDATE attempts SET status = 'abandoned' "
            "WHERE status = 'completed' "
            "AND listening_band IS NULL "
            "AND reading_band IS NULL "
            "AND writing_band IS NULL "
            "AND speaking_band IS NULL "
            "AND updated_at < :cutoff"
        ),
        {"cutoff": now - timedelta(hours=1)},
    )

    # 3. Legacy writing_band = 0 → NULL
    r3 = conn.execute(
        sa.text(
            "UPDATE attempts SET writing_band = NULL "
            "WHERE writing_band = 0"
        ),
    )

    # 4. Stuck auto_scored with speaking_session in_progress >1h
    r4_attempts = conn.execute(
        sa.text(
            "UPDATE attempts SET status = 'completed_without_speaking' "
            "WHERE status = 'auto_scored' "
            "AND id IN ("
            "  SELECT a.id FROM attempts a "
            "  JOIN speaking_sessions ss ON ss.attempt_id = a.id "
            "  WHERE a.status = 'auto_scored' "
            "  AND ss.status = 'in_progress' "
            "  AND ss.updated_at < :cutoff"
            ")"
        ),
        {"cutoff": now - timedelta(hours=1)},
    )
    r4_sessions = conn.execute(
        sa.text(
            "UPDATE speaking_sessions SET status = 'abandoned' "
            "WHERE status = 'in_progress' "
            "AND updated_at < :cutoff "
            "AND attempt_id IS NOT NULL"
        ),
        {"cutoff": now - timedelta(hours=1)},
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Remap new statuses back to originals
    conn.execute(
        sa.text(
            "UPDATE attempts SET status = 'completed' "
            "WHERE status = 'completed_without_speaking'"
        ),
    )
    conn.execute(
        sa.text(
            "UPDATE attempts SET status = 'auto_scored' "
            "WHERE status = 'speaking_in_progress'"
        ),
    )
    conn.execute(
        sa.text(
            "UPDATE attempts SET status = 'completed' "
            "WHERE status = 'partial'"
        ),
    )

    op.alter_column(
        "attempts", "status",
        type_=sa.String(20),
        existing_type=sa.String(32),
    )
