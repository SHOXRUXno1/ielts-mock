"""canonicalize speaking_part content to canonical schema

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-07-08

For each speaking section (by order position among its test's speaking sections):
- Part 1/3: collapse multiple legacy {prompt} rows into one {part, questions:[]}
- Part 2: wrap legacy {topic, bullets} into {part:2, cue_card:{...}}
- Skip rows already in canonical form (has 'questions' list or 'cue_card' as object)
"""
import json

from alembic import op
from sqlalchemy import text

revision = "f2a3b4c5d6e7"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    sections = conn.execute(text("""
        SELECT s.id, s.test_id, s.order,
               ROW_NUMBER() OVER (PARTITION BY s.test_id ORDER BY s.order) AS part_num
        FROM sections s
        WHERE s.type = 'speaking'
        ORDER BY s.test_id, s.order
    """)).fetchall()

    for section_row in sections:
        section_id = str(section_row[0])
        part_num = int(section_row[3])

        questions = conn.execute(text("""
            SELECT id, content, "order"
            FROM questions
            WHERE section_id = :sid
            ORDER BY "order"
        """), {"sid": section_id}).fetchall()

        if not questions:
            continue

        first_content = questions[0][1] if isinstance(questions[0][1], dict) else {}

        # Already canonical — skip
        if isinstance(first_content.get("questions"), list):
            continue
        if isinstance(first_content.get("cue_card"), dict):
            continue

        if part_num == 2:
            # Wrap legacy {topic, bullets} or {cue_card: str} into canonical cue_card shape
            content = questions[0][1] if isinstance(questions[0][1], dict) else {}
            topic = content.get("topic", "")
            bullets = content.get("bullets", [])
            if isinstance(bullets, str):
                bullets = [b.strip() for b in bullets.split("\n") if b.strip()]
            if not topic and "cue_card" in content:
                topic = str(content["cue_card"])

            new_content = {"part": 2, "cue_card": {"topic": topic, "bullets": bullets}}

            conn.execute(text("""
                UPDATE questions
                SET content = CAST(:content AS jsonb)
                WHERE id = :qid
            """), {"content": json.dumps(new_content), "qid": str(questions[0][0])})

            for extra in questions[1:]:
                conn.execute(
                    text("DELETE FROM questions WHERE id = :qid"),
                    {"qid": str(extra[0])},
                )
        else:
            # Collapse legacy {prompt} rows into one canonical {part, questions:[]}
            prompts = []
            canonical_id = None
            for q in questions:
                c = q[1] if isinstance(q[1], dict) else {}
                if isinstance(c.get("questions"), list):
                    # Already partially canonical; collect and mark
                    prompts.extend(str(p) for p in c["questions"])
                    if canonical_id is None:
                        canonical_id = str(q[0])
                    continue
                prompt = c.get("prompt", "")
                if prompt:
                    prompts.append(str(prompt))

            new_content = {"part": part_num, "questions": prompts}
            target_id = canonical_id or str(questions[0][0])

            conn.execute(text("""
                UPDATE questions
                SET content = CAST(:content AS jsonb)
                WHERE id = :qid
            """), {"content": json.dumps(new_content), "qid": target_id})

            # Delete all other questions in the section
            for q in questions:
                if str(q[0]) != target_id:
                    conn.execute(
                        text("DELETE FROM questions WHERE id = :qid"),
                        {"qid": str(q[0])},
                    )


def downgrade():
    # No downgrade — legacy data was fragile; admins re-enter if needed
    pass
