"""add book_slug and test_number to tests

Revision ID: a1b2c3d4e5f7
Revises: f6a7b8c9d0e1
Create Date: 2026-07-07 22:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f7"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns as nullable first so existing rows don't violate constraints
    op.add_column("tests", sa.Column("book_slug", sa.String(255), nullable=True))
    op.add_column("tests", sa.Column("test_number", sa.Integer(), nullable=True))

    # Populate book_slug from book_name (slugified) or title as fallback,
    # then assign test_number as row_number per slug group ordered by created_at.
    op.execute(
        """
        WITH slugged AS (
            SELECT
                id,
                LOWER(
                    REGEXP_REPLACE(
                        REGEXP_REPLACE(
                            REGEXP_REPLACE(
                                TRIM(COALESCE(book_name, title)),
                                '[^a-z0-9\\s-]', '', 'gi'
                            ),
                            '[\\s]+', '-', 'g'
                        ),
                        '-+', '-', 'g'
                    )
                ) AS computed_slug
            FROM tests
        ),
        numbered AS (
            SELECT
                s.id,
                TRIM(BOTH '-' FROM s.computed_slug) AS book_slug,
                ROW_NUMBER() OVER (
                    PARTITION BY TRIM(BOTH '-' FROM s.computed_slug)
                    ORDER BY t.created_at
                ) AS test_number
            FROM slugged s
            JOIN tests t ON t.id = s.id
        )
        UPDATE tests
        SET
            book_slug   = numbered.book_slug,
            test_number = numbered.test_number
        FROM numbered
        WHERE tests.id = numbered.id
        """
    )

    # Fill any remaining NULLs (edge case: empty title)
    op.execute("UPDATE tests SET book_slug = 'untitled', test_number = 1 WHERE book_slug IS NULL OR book_slug = ''")

    # Now make columns NOT NULL
    op.alter_column("tests", "book_slug", nullable=False)
    op.alter_column("tests", "test_number", nullable=False)

    # Index + unique constraint
    op.create_index("ix_tests_book_slug", "tests", ["book_slug"])
    op.create_unique_constraint("uq_book_test", "tests", ["book_slug", "test_number"])


def downgrade() -> None:
    op.drop_constraint("uq_book_test", "tests", type_="unique")
    op.drop_index("ix_tests_book_slug", table_name="tests")
    op.drop_column("tests", "test_number")
    op.drop_column("tests", "book_slug")
