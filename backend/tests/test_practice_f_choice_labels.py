"""Choice labels belong to the UI, not to MCQ/multi-select option text."""

import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from app.models.question import QuestionType  # noqa: E402
from seed_practice_f_listening import build_part, choice_texts  # noqa: E402


def test_choice_labels_are_removed_once_and_idempotently():
    options = ["A. sleeping bag", "B) tent", "C. food"]
    expected = ["sleeping bag", "tent", "food"]
    assert choice_texts(options) == expected
    assert choice_texts(expected) == expected
    assert options[0] == "A. sleeping bag"
    assert choice_texts(["A good answer", "B.B. initials"]) == [
        "A good answer", "B.B. initials"
    ]


@pytest.mark.parametrize("test_number", range(1, 7))
@pytest.mark.parametrize("part", range(1, 5))
def test_all_choice_options_are_unlabelled_but_matching_lists_keep_labels(
    test_number, part
):
    _, groups = build_part(test_number, part, uuid.uuid4())
    for group in groups:
        for question in group.questions:
            if question.question_type in {QuestionType.MCQ, QuestionType.MULTI_SELECT}:
                options = question.content["options"]
                assert options == choice_texts(options)
        if (group.options_shared or {}).get("options"):
            # Do not remove matching labels used as dropdown values.
            assert all(
                option.split(".", 1)[0].strip().isalpha()
                for option in group.options_shared["options"]
            )
