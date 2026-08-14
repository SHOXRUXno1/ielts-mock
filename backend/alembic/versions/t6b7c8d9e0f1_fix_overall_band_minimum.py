"""Null out overall_band where fewer than 3 section bands exist.

Revision ID: t6b7c8d9e0f1
Revises: s5a6b7c8d9e0
Create Date: 2026-07-13

IELTS overall band requires at least 3 sections. Rows that were
computed from 1-2 bands now get overall_band = NULL.
"""

from alembic import op
import sqlalchemy as sa

revision = "t6b7c8d9e0f1"
down_revision = "s5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE attempts
        SET overall_band = NULL
        WHERE overall_band IS NOT NULL
          AND (
            (CASE WHEN listening_band IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN reading_band   IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN writing_band   IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN speaking_band  IS NOT NULL THEN 1 ELSE 0 END)
          ) < 3
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE attempts
        SET overall_band = ROUND(
            COALESCE(
                (
                    COALESCE(listening_band, 0) * (CASE WHEN listening_band IS NOT NULL THEN 1 ELSE 0 END) +
                    COALESCE(reading_band,   0) * (CASE WHEN reading_band   IS NOT NULL THEN 1 ELSE 0 END) +
                    COALESCE(writing_band,   0) * (CASE WHEN writing_band   IS NOT NULL THEN 1 ELSE 0 END) +
                    COALESCE(speaking_band,  0) * (CASE WHEN speaking_band  IS NOT NULL THEN 1 ELSE 0 END)
                )::numeric / NULLIF(
                    (CASE WHEN listening_band IS NOT NULL THEN 1 ELSE 0 END) +
                    (CASE WHEN reading_band   IS NOT NULL THEN 1 ELSE 0 END) +
                    (CASE WHEN writing_band   IS NOT NULL THEN 1 ELSE 0 END) +
                    (CASE WHEN speaking_band  IS NOT NULL THEN 1 ELSE 0 END),
                    0
                )
            ) * 2
        ) / 2.0
        WHERE overall_band IS NULL
          AND (
            (CASE WHEN listening_band IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN reading_band   IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN writing_band   IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN speaking_band  IS NOT NULL THEN 1 ELSE 0 END)
          ) BETWEEN 1 AND 2
    """))
