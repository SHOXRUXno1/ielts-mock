"""_upsert_answers must write a batch in one statement (Finish section)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from app.api.attempts import _upsert_answers
from app.schemas.attempt import AnswerSubmit


@pytest.mark.asyncio
async def test_upsert_answers_uses_single_statement():
    db = AsyncMock()
    attempt_id = uuid.uuid4()
    answers = [
        AnswerSubmit(question_id=uuid.uuid4(), response={"answer": str(i)})
        for i in range(40)
    ]

    saved = await _upsert_answers(db, attempt_id, answers)

    assert saved == 40
    assert db.execute.await_count == 1


@pytest.mark.asyncio
async def test_upsert_answers_dedupes_question_id():
    db = AsyncMock()
    qid = uuid.uuid4()
    answers = [
        AnswerSubmit(question_id=qid, response={"answer": "old"}),
        AnswerSubmit(question_id=qid, response={"answer": "new"}),
    ]

    saved = await _upsert_answers(db, uuid.uuid4(), answers)

    assert saved == 1
    assert db.execute.await_count == 1
