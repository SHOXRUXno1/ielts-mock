"""Remove sample_answer from essay question content.

Revision ID: i5c6d7e8f9a0
Revises: h4b5c6d7e8f9
Create Date: 2026-07-09
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "i5c6d7e8f9a0"
down_revision: Union[str, None] = "h4b5c6d7e8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE questions
        SET content = content - 'sample_answer'
        WHERE question_type = 'essay'
          AND content ? 'sample_answer'
        """
    )


def downgrade() -> None:
    # Irreversible cleanup — sample_answer feature was removed.
    pass
