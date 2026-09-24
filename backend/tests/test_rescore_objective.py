import uuid
from types import SimpleNamespace

from scripts.rescore_objective import (
    _canonicalize_choice_answers,
    _choice_tokens,
    _score_objective_section,
    _target_sections,
)


def test_target_sections_expands_both_objective_skills():
    assert _target_sections("both") == {"listening", "reading"}
    assert _target_sections("reading") == {"reading"}


def test_legacy_three_choice_response_is_canonicalized():
    question_id = uuid.uuid4()
    question = SimpleNamespace(question_type="true_false_ng", id=question_id)
    answer = SimpleNamespace(response={"answer": "Not Given"})
    section = SimpleNamespace(questions=[question])

    _canonicalize_choice_answers(section, {question_id: answer})

    assert answer.response == {"answer": "NOT GIVEN"}


def test_legacy_three_choice_answer_is_scored_case_insensitively():
    question_id = uuid.uuid4()
    question = SimpleNamespace(
        id=question_id,
        question_type="true_false_ng",
        answer_key={"correct": "NOT GIVEN"},
    )
    answer = SimpleNamespace(
        question_id=question_id,
        response={"answer": "Not Given"},
        is_correct=None,
        score=None,
    )

    assert _score_objective_section([question], [answer]) == (1, 1)
    assert answer.is_correct is True
    assert answer.score == 1.0


def test_three_choice_fallback_does_not_depend_on_a_legacy_question_type():
    question_id = uuid.uuid4()
    question = SimpleNamespace(
        id=question_id,
        question_type="legacy_unknown_type",
        answer_key={"answer": "FALSE"},
    )
    answer = SimpleNamespace(
        question_id=question_id,
        response={"answer": "False"},
        is_correct=None,
        score=None,
    )

    assert _score_objective_section([question], [answer]) == (1, 1)
    assert answer.is_correct is True


def test_choice_tokens_reads_nested_legacy_answer_keys():
    assert _choice_tokens({"accepted": ["FALSE", "Not Given"]}) == {
        "FALSE",
        "NOT GIVEN",
    }
