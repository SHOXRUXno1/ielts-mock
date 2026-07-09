"""add question_groups table with section.title and question.question_group_id

Revision ID: c1d2e3f4a5b6
Revises: a1b2c3d4e5f7
Create Date: 2026-07-08 09:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "a1b2c3d4e5f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create question_groups table
    op.create_table(
        "question_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order", sa.SmallInteger(), nullable=False),
        sa.Column("question_type", sa.String(50), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False, server_default=""),
        sa.Column("options_shared", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_question_groups_section_id", "question_groups", ["section_id"])

    # 2. Add columns to existing tables
    op.add_column(
        "questions",
        sa.Column(
            "question_group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("question_groups.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column("sections", sa.Column("title", sa.String(255), nullable=True))

    # 3. Back-fill groups for existing questions (contiguous runs of same question_type per section)
    conn = op.get_bind()

    # Fetch all section ids that have questions
    sections = conn.execute(
        sa.text(
            "SELECT DISTINCT section_id FROM questions ORDER BY section_id"
        )
    ).fetchall()

    for (section_id,) in sections:
        questions = conn.execute(
            sa.text(
                'SELECT id, question_type FROM questions '
                'WHERE section_id = :sid ORDER BY "order"'
            ),
            {"sid": section_id},
        ).fetchall()

        if not questions:
            continue

        group_order = 0
        current_type = None
        current_group_id = None

        for q_id, q_type in questions:
            if q_type != current_type:
                # Start a new group
                group_order += 1
                current_type = q_type
                result = conn.execute(
                    sa.text(
                        "INSERT INTO question_groups "
                        "(id, section_id, \"order\", question_type, instruction, created_at, updated_at) "
                        "VALUES (gen_random_uuid(), :sid, :ord, :qtype, '', now(), now()) "
                        "RETURNING id"
                    ),
                    {"sid": section_id, "ord": group_order, "qtype": q_type},
                )
                current_group_id = result.fetchone()[0]

            conn.execute(
                sa.text(
                    "UPDATE questions SET question_group_id = :gid WHERE id = :qid"
                ),
                {"gid": current_group_id, "qid": q_id},
            )

    # 4. Check constraint: question must have either group_id or question_type (always true since question_type stays NOT NULL)
    op.create_check_constraint(
        "ck_question_group_or_type",
        "questions",
        "question_group_id IS NOT NULL OR question_type IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_constraint("ck_question_group_or_type", "questions", type_="check")
    op.drop_column("sections", "title")
    op.drop_column("questions", "question_group_id")
    op.drop_index("ix_question_groups_section_id", table_name="question_groups")
    op.drop_table("question_groups")
