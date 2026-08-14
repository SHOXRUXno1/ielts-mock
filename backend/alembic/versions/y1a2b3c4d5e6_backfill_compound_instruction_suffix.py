"""backfill compound instruction suffix 'for each answer.'

Revision ID: y1a2b3c4d5e6
Revises: x0f1a2b3c4d5
Create Date: 2026-07-20
"""

from alembic import op
import sqlalchemy as sa

revision = "y1a2b3c4d5e6"
down_revision = "x0f1a2b3c4d5"
branch_labels = None
depends_on = None

COMPOUND_TYPES = (
    "table_completion",
    "note_completion",
    "form_completion",
    "summary_completion",
    "flow_chart_completion",
)


def upgrade() -> None:
    conn = op.get_bind()
    for qtype in COMPOUND_TYPES:
        # Replace trailing '.' with ' for each answer.' for compound groups
        # that end with a word-limit phrase followed by period
        conn.execute(
            sa.text(
                """
                UPDATE question_groups
                SET instruction = LEFT(instruction, LENGTH(instruction) - 1)
                                  || ' for each answer.'
                WHERE question_type = :qtype
                  AND instruction != ''
                  AND instruction NOT LIKE '%for each answer.'
                  AND instruction LIKE '%.'
                """
            ),
            {"qtype": qtype},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for qtype in COMPOUND_TYPES:
        # Remove ' for each answer.' and restore trailing '.'
        conn.execute(
            sa.text(
                """
                UPDATE question_groups
                SET instruction = LEFT(instruction,
                                       LENGTH(instruction) - LENGTH(' for each answer.'))
                                  || '.'
                WHERE question_type = :qtype
                  AND instruction LIKE '%for each answer.'
                """
            ),
            {"qtype": qtype},
        )
