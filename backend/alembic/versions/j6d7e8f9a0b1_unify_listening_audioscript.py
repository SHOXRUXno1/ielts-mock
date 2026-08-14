"""Unify listening audioscript storage (passage -> audioscript).

Revision ID: j6d7e8f9a0b1
Revises: i5c6d7e8f9a0
Create Date: 2026-07-10
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "j6d7e8f9a0b1"
down_revision: Union[str, None] = "i5c6d7e8f9a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Move legacy listening transcripts from passage into audioscript.
    op.execute(
        """
        UPDATE sections
        SET audioscript = passage, passage = NULL
        WHERE type = 'listening'
          AND passage IS NOT NULL
          AND audioscript IS NULL
        """
    )


def downgrade() -> None:
    # Reverse: move audioscript back to passage for listening sections
    # that have no passage yet.
    op.execute(
        """
        UPDATE sections
        SET passage = audioscript, audioscript = NULL
        WHERE type = 'listening'
          AND audioscript IS NOT NULL
          AND passage IS NULL
        """
    )
