"""Require every question to belong to a question group.

Revision ID: z2b3c4d5e6f7
Revises: y1a2b3c4d5e6
Create Date: 2026-07-23

Orphan Listening/Reading gaps (``question_group_id IS NULL``) previously
surfaced in the take UI as ghost rows and inflated display numbering.
This migration:
  1. Wraps leftover Speaking orphans in a group
  2. Deletes Listening/Reading orphans (answers cascade)
  3. Makes ``questions.question_group_id`` NOT NULL
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "z2b3c4d5e6f7"
down_revision: Union[str, None] = "y1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Speaking: create a wrapper group per section that still has orphans
    #    and attach those rows.
    op.execute(
        """
        INSERT INTO question_groups (
            id, section_id, "order", question_type, instruction,
            options_shared, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            s.id,
            1,
            'speaking_part',
            '',
            NULL,
            NOW(),
            NOW()
        FROM sections s
        WHERE s.type = 'speaking'
          AND EXISTS (
              SELECT 1 FROM questions q
              WHERE q.section_id = s.id
                AND q.question_group_id IS NULL
          )
          AND NOT EXISTS (
              SELECT 1 FROM question_groups g
              WHERE g.section_id = s.id
          )
        """
    )
    op.execute(
        """
        UPDATE questions AS q
        SET question_group_id = g.id
        FROM question_groups AS g
        JOIN sections AS s ON s.id = g.section_id
        WHERE q.section_id = g.section_id
          AND q.question_group_id IS NULL
          AND s.type = 'speaking'
          AND g.question_type = 'speaking_part'
        """
    )

    # 2) Listening / Reading orphans are data bugs — drop them.
    op.execute(
        """
        DELETE FROM questions q
        USING sections s
        WHERE q.section_id = s.id
          AND q.question_group_id IS NULL
          AND s.type IN ('listening', 'reading')
        """
    )

    # 3) Anything still orphaned (e.g. writing) gets a generic wrapper.
    op.execute(
        """
        INSERT INTO question_groups (
            id, section_id, "order", question_type, instruction,
            options_shared, created_at, updated_at
        )
        SELECT
            gen_random_uuid(),
            s.id,
            COALESCE((SELECT MAX(g."order") FROM question_groups g WHERE g.section_id = s.id), 0) + 1,
            COALESCE(
                (
                    SELECT q.question_type::text
                    FROM questions q
                    WHERE q.section_id = s.id AND q.question_group_id IS NULL
                    ORDER BY q."order"
                    LIMIT 1
                ),
                'mcq'
            ),
            '',
            NULL,
            NOW(),
            NOW()
        FROM sections s
        WHERE EXISTS (
            SELECT 1 FROM questions q
            WHERE q.section_id = s.id
              AND q.question_group_id IS NULL
        )
        """
    )
    op.execute(
        """
        UPDATE questions AS q
        SET question_group_id = g.id
        FROM (
            SELECT DISTINCT ON (section_id) id, section_id
            FROM question_groups
            ORDER BY section_id, "order" DESC
        ) AS g
        WHERE q.section_id = g.section_id
          AND q.question_group_id IS NULL
        """
    )

    op.alter_column("questions", "question_group_id", nullable=False)


def downgrade() -> None:
    op.alter_column("questions", "question_group_id", nullable=True)
