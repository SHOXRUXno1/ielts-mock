"""Split writing content.prompt into task_description + task_instruction.

Data-only migration (no schema changes). Parses existing content.prompt,
matches trailing instruction against known IELTS presets, and writes
task_description + task_instruction back into the JSONB content field.
Preserves content.prompt as-is for backward compatibility.

Revision ID: w9e0f1a2b3c4
Revises: v8d9e0f1a2b3
Create Date: 2026-07-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "w9e0f1a2b3c4"
down_revision = "v8d9e0f1a2b3"
branch_labels = None
depends_on = None

KNOWN_INSTRUCTIONS = [
    "Discuss both these views and give your own opinion. "
    "Give reasons for your answer and include any relevant examples "
    "from your own knowledge or experience.",
    "Summarise the information by selecting and reporting the main features, "
    "and make comparisons where relevant.",
    "Give reasons for your answer and include any relevant examples "
    "from your own knowledge or experience.",
]


def _split_prompt(prompt: str, existing_instruction: str | None) -> tuple[str, str | None]:
    """Split a prompt into (description, instruction).

    If an instruction key already exists from import, use it directly.
    Otherwise try to match the tail of the prompt against known instructions.
    """
    if existing_instruction:
        return prompt, existing_instruction

    if not prompt:
        return "", None

    for instr in KNOWN_INSTRUCTIONS:
        if prompt.rstrip().endswith(instr):
            desc = prompt[: prompt.rindex(instr)].rstrip()
            return desc, instr

    lower = prompt.lower().rstrip()
    for instr in KNOWN_INSTRUCTIONS:
        if lower.endswith(instr.lower()):
            idx = lower.rindex(instr.lower())
            desc = prompt[:idx].rstrip()
            actual_instr = prompt[idx:].rstrip()
            return desc, actual_instr

    return prompt, None


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, content FROM questions "
            "WHERE question_type = 'essay' AND content IS NOT NULL"
        )
    ).fetchall()

    for row in rows:
        qid = row[0]
        content = row[1]
        if not isinstance(content, dict):
            continue
        if "task_description" in content:
            continue

        prompt = content.get("prompt", "")
        existing_instr = content.get("instruction")
        desc, instr = _split_prompt(prompt, existing_instr)

        new_content = dict(content)
        new_content["task_description"] = desc
        if instr:
            new_content["task_instruction"] = instr

        conn.execute(
            sa.text("UPDATE questions SET content = :content WHERE id = :id"),
            {"content": sa.type_coerce(new_content, JSONB), "id": qid},
        )


def downgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, content FROM questions "
            "WHERE question_type = 'essay' AND content IS NOT NULL"
        )
    ).fetchall()

    for row in rows:
        qid = row[0]
        content = row[1]
        if not isinstance(content, dict):
            continue

        new_content = {k: v for k, v in content.items()
                       if k not in ("task_description", "task_instruction")}

        conn.execute(
            sa.text("UPDATE questions SET content = :content WHERE id = :id"),
            {"content": sa.type_coerce(new_content, JSONB), "id": qid},
        )
