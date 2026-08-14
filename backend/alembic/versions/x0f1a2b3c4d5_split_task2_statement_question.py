"""Split Task 2 task_description into task_statement + task_question.

Data-only migration. For Task 2 essay questions, tries to match the
trailing sentence of task_description against known question presets and
splits into task_statement + task_question. Preserves task_description
for backward compatibility.

Revision ID: x0f1a2b3c4d5
Revises: w9e0f1a2b3c4
Create Date: 2026-07-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "x0f1a2b3c4d5"
down_revision = "w9e0f1a2b3c4"
branch_labels = None
depends_on = None

KNOWN_QUESTIONS = [
    "To what extent do you agree or disagree with this statement?",
    "Discuss both these views and give your own opinion.",
    "What problems does this cause and what solutions can you suggest?",
    "Discuss the advantages and disadvantages.",
    "What are the reasons for this? What can be done to address it?",
    "To what extent do you agree or disagree?",
]


def _split_description(desc: str) -> tuple[str, str | None]:
    if not desc:
        return "", None

    for q in KNOWN_QUESTIONS:
        if desc.rstrip().endswith(q):
            statement = desc[: desc.rindex(q)].rstrip()
            return statement, q

    lower = desc.lower().rstrip()
    for q in KNOWN_QUESTIONS:
        if lower.endswith(q.lower()):
            idx = lower.rindex(q.lower())
            statement = desc[:idx].rstrip()
            actual_q = desc[idx:].rstrip()
            return statement, actual_q

    return desc, None


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, content FROM questions "
            "WHERE question_type = 'essay' "
            "AND content IS NOT NULL "
            "AND (task_number = 2 OR content->>'task_number' = '2')"
        )
    ).fetchall()

    for row in rows:
        qid = row[0]
        content = row[1]
        if not isinstance(content, dict):
            continue
        if "task_statement" in content:
            continue

        desc = content.get("task_description") or content.get("prompt", "")
        statement, question = _split_description(desc)

        new_content = dict(content)
        new_content["task_statement"] = statement
        if question:
            new_content["task_question"] = question
        if statement and question:
            new_content["task_description"] = f"{statement}\n\n{question}"

        conn.execute(
            sa.text("UPDATE questions SET content = :content WHERE id = :id"),
            {"content": sa.type_coerce(new_content, JSONB), "id": qid},
        )


def downgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, content FROM questions "
            "WHERE question_type = 'essay' "
            "AND content IS NOT NULL "
            "AND (task_number = 2 OR content->>'task_number' = '2')"
        )
    ).fetchall()

    for row in rows:
        qid = row[0]
        content = row[1]
        if not isinstance(content, dict):
            continue

        new_content = {k: v for k, v in content.items()
                       if k not in ("task_statement", "task_question", "use_custom_question")}

        conn.execute(
            sa.text("UPDATE questions SET content = :content WHERE id = :id"),
            {"content": sa.type_coerce(new_content, JSONB), "id": qid},
        )
