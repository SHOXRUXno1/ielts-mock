"""rename task_achievement to task_response in task_2 writing results

Revision ID: e1f2a3b4c5d6
Revises: d2e3f4a5b6c7
Create Date: 2026-07-08

"""
from alembic import op

revision = "e1f2a3b4c5d6"
down_revision = "d2e3f4a5b6c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # For each writing evaluation job whose task_2 result has task_achievement,
    # rename it to task_response.
    op.execute("""
        UPDATE evaluation_jobs
        SET result = jsonb_set(
            result #- '{tasks,task_2,task_achievement}',
            '{tasks,task_2,task_response}',
            result->'tasks'->'task_2'->'task_achievement'
        )
        WHERE section_type = 'writing'
          AND result IS NOT NULL
          AND result->'tasks'->'task_2' ? 'task_achievement'
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE evaluation_jobs
        SET result = jsonb_set(
            result #- '{tasks,task_2,task_response}',
            '{tasks,task_2,task_achievement}',
            result->'tasks'->'task_2'->'task_response'
        )
        WHERE section_type = 'writing'
          AND result IS NOT NULL
          AND result->'tasks'->'task_2' ? 'task_response'
    """)
