"""Give Cambridge IELTS 9 Test 4 listening Q9 a real answer.

Revision ID: g8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-08-24

The question asks for the time in "Avoiding injuries during exercise —
9th March at ___", and its key was seeded as ["$n/a", "unavailable"], a
placeholder left in by whoever built the test. Neither string is a time, so
the question could not be answered correctly by anybody: every candidate lost
that mark whatever they wrote, and the report showed them "$n/a | unavailable"
as the answer they should have given.

The recording says "it's a late afternoon talk, at four thirty", so the key is
4.30, with the spellings a candidate might reasonably use.

Only this question is touched, and only while it still holds the placeholder,
so the migration is safe to re-run. Any other placeholder key is reported and
left alone — the right answer differs per question and cannot be guessed here.
"""

from __future__ import annotations

import json
import logging
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "g8b9c0d1e2f3"
down_revision: Union[str, None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.runtime.migration")

PLACEHOLDER = "$n/a"

ANSWER_KEY = {
    "correct": [
        "4.30",
        "4:30",
        "4.30pm",
        "4.30 pm",
        "4:30pm",
        "4:30 pm",
        "16.30",
        "16:30",
        "four thirty",
    ]
}


def upgrade() -> None:
    conn = op.get_bind()

    result = conn.execute(
        text(
            """
            UPDATE questions q
            SET answer_key = CAST(:answer_key AS jsonb)
            FROM sections s
            JOIN tests t ON t.id = s.test_id
            WHERE q.section_id = s.id
              AND t.title LIKE 'Cambridge IELTS 9%Test 4'
              AND s.type = 'listening'
              AND s."order" = 1
              AND q."order" = 9
              AND q.answer_key::text LIKE :placeholder
            """
        ),
        {"answer_key": json.dumps(ANSWER_KEY), "placeholder": f"%{PLACEHOLDER}%"},
    )
    if result.rowcount:
        logger.info("Repaired the placeholder answer key on %s question(s).", result.rowcount)

    leftovers = conn.execute(
        text(
            """
            SELECT q.id::text AS question_id,
                   t.title AS test_title,
                   s.type::text AS section_type,
                   s."order" AS section_order,
                   q."order" AS question_order,
                   q.answer_key::text AS answer_key
            FROM questions q
            JOIN sections s ON s.id = q.section_id
            JOIN tests t ON t.id = s.test_id
            WHERE q.answer_key::text LIKE :placeholder
            ORDER BY t.title, s."order", q."order"
            """
        ),
        {"placeholder": f"%{PLACEHOLDER}%"},
    ).fetchall()

    for row in leftovers:
        logger.warning(
            "Question still has a placeholder answer key and cannot be answered: "
            "test=%r %s part %s question %s id=%s key=%s",
            row.test_title,
            row.section_type,
            row.section_order,
            row.question_order,
            row.question_id,
            row.answer_key,
        )


def downgrade() -> None:
    # The previous value was a placeholder, not an answer; restoring it would
    # only make the question unanswerable again.
    pass
