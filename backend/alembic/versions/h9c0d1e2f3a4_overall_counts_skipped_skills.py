"""Count skipped skills as 0 in the full-mock overall.

Revision ID: h9c0d1e2f3a4
Revises: g8b9c0d1e2f3
Create Date: 2026-08-27

Overall used to average only the skills that had a band, so skipping
Speaking left L/R/W untouched: (5+5+5)/3 = 5.0. Official IELTS overall
is always four skills. A skip is 0, so that paper is 4.0.

Rows still waiting on a writing/speaking job stay NULL — those skills
are in flight, not skipped.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "h9c0d1e2f3a4"
down_revision: Union[str, None] = "g8b9c0d1e2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NEW_OVERALL = """
FLOOR((
    COALESCE(listening_band, 0) +
    COALESCE(reading_band, 0) +
    COALESCE(writing_band, 0) +
    COALESCE(speaking_band, 0)
)::numeric / 4 * 2 + 0.5) / 2
"""

_OLD_OVERALL = """
ROUND((
    COALESCE(listening_band, 0) * (CASE WHEN listening_band IS NOT NULL THEN 1 ELSE 0 END) +
    COALESCE(reading_band, 0) * (CASE WHEN reading_band IS NOT NULL THEN 1 ELSE 0 END) +
    COALESCE(writing_band, 0) * (CASE WHEN writing_band IS NOT NULL THEN 1 ELSE 0 END) +
    COALESCE(speaking_band, 0) * (CASE WHEN speaking_band IS NOT NULL THEN 1 ELSE 0 END)
)::numeric / NULLIF(
    (CASE WHEN listening_band IS NOT NULL THEN 1 ELSE 0 END) +
    (CASE WHEN reading_band IS NOT NULL THEN 1 ELSE 0 END) +
    (CASE WHEN writing_band IS NOT NULL THEN 1 ELSE 0 END) +
    (CASE WHEN speaking_band IS NOT NULL THEN 1 ELSE 0 END),
    0
) * 2) / 2.0
"""

_SCORED_FULL_MOCK = """
    (mode = 'full_mock' OR mode IS NULL)
    AND (
        listening_band IS NOT NULL
        OR reading_band IS NOT NULL
        OR writing_band IS NOT NULL
        OR speaking_band IS NOT NULL
    )
    AND NOT EXISTS (
        SELECT 1 FROM evaluation_jobs j
        WHERE j.attempt_id = attempts.id
          AND j.status IN ('pending', 'processing')
    )
"""


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text(f"""
        UPDATE attempts
        SET overall_band = {_NEW_OVERALL}
        WHERE {_SCORED_FULL_MOCK}
    """))
    conn.execute(text("""
        UPDATE attempts
        SET overall_band = NULL
        WHERE (mode = 'full_mock' OR mode IS NULL)
          AND EXISTS (
            SELECT 1 FROM evaluation_jobs j
            WHERE j.attempt_id = attempts.id
              AND j.status IN ('pending', 'processing')
          )
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text(f"""
        UPDATE attempts
        SET overall_band = CASE
            WHEN (
                (CASE WHEN listening_band IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN reading_band IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN writing_band IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN speaking_band IS NOT NULL THEN 1 ELSE 0 END)
            ) < 3 THEN NULL
            ELSE {_OLD_OVERALL}
        END
        WHERE {_SCORED_FULL_MOCK}
    """))
