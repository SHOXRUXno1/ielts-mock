import uuid
from types import SimpleNamespace

from scripts.rescore_objective import _canonicalize_choice_answers, _target_sections


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
