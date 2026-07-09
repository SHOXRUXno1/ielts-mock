"""Tests for auto-scoring logic (scoring.py).

Covers:
  - MCQ: canonical "correct" key, legacy "answer" key
  - T/F/NG: canonical and legacy
  - gap_fill: single correct, list of variants, case insensitivity
  - matching: partial credit per pair, both dict-correct and legacy answers[]
  - score_section: aggregates sub-items correctly
  - band tables: raw->band boundary values for Listening and Reading
"""

import uuid
from types import SimpleNamespace

import pytest

from app.models.question import QuestionType
from app.services.scoring import (
    check_answer,
    correct_to_listening_band,
    correct_to_reading_band,
    score_answer,
    score_section,
)


# ── Helpers ────────────────────────────────────────────────────────────────────
# Use SimpleNamespace so we avoid SQLAlchemy instrumentation overhead in unit tests.

def make_q(
    qtype: QuestionType,
    answer_key: dict | None,
    content: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        order=1,
        question_type=qtype,
        answer_key=answer_key,
        content=content or {},
    )


def make_a(question: SimpleNamespace, response: dict) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        question_id=question.id,
        attempt_id=uuid.uuid4(),
        response=response,
        is_correct=None,
        score=None,
    )


# ── MCQ ────────────────────────────────────────────────────────────────────────

class TestMCQ:
    def test_correct_key_correct(self):
        q = make_q(QuestionType.MCQ, {"correct": "Paris"})
        a = make_a(q, {"answer": "Paris"})
        c, t = score_answer(q, a)
        assert (c, t) == (1, 1)
        assert a.is_correct is True

    def test_correct_key_wrong(self):
        q = make_q(QuestionType.MCQ, {"correct": "Paris"})
        a = make_a(q, {"answer": "London"})
        c, t = score_answer(q, a)
        assert (c, t) == (0, 1)
        assert a.is_correct is False

    def test_legacy_answer_key(self):
        """Legacy seed format: answer_key={"answer": "..."}"""
        q = make_q(QuestionType.MCQ, {"answer": "Paris"})
        a = make_a(q, {"answer": "Paris"})
        c, t = score_answer(q, a)
        assert (c, t) == (1, 1)

    def test_case_insensitive(self):
        q = make_q(QuestionType.MCQ, {"correct": "TRUE"})
        a = make_a(q, {"answer": "true"})
        assert check_answer(q, a) is True

    def test_whitespace_trimmed(self):
        q = make_q(QuestionType.MCQ, {"correct": "  Paris  "})
        a = make_a(q, {"answer": "Paris"})
        assert check_answer(q, a) is True


# ── T/F/NG ─────────────────────────────────────────────────────────────────────

class TestTrueFalseNG:
    def test_true_correct(self):
        q = make_q(QuestionType.TRUE_FALSE_NG, {"correct": "True"})
        a = make_a(q, {"answer": "True"})
        assert check_answer(q, a) is True

    def test_legacy_answer_key(self):
        q = make_q(QuestionType.TRUE_FALSE_NG, {"answer": "Not Given"})
        a = make_a(q, {"answer": "Not Given"})
        assert check_answer(q, a) is True

    def test_false_incorrect(self):
        q = make_q(QuestionType.TRUE_FALSE_NG, {"correct": "False"})
        a = make_a(q, {"answer": "True"})
        assert check_answer(q, a) is False


# ── Gap fill ───────────────────────────────────────────────────────────────────

class TestGapFill:
    def test_single_correct(self):
        q = make_q(QuestionType.GAP_FILL, {"correct": "architecture"})
        a = make_a(q, {"answer": "architecture"})
        assert check_answer(q, a) is True

    def test_variant_list(self):
        q = make_q(QuestionType.GAP_FILL, {"correct": ["10", "ten"]})
        a = make_a(q, {"answer": "ten"})
        assert check_answer(q, a) is True

    def test_case_insensitive_gap(self):
        q = make_q(QuestionType.GAP_FILL, {"correct": "Architecture"})
        a = make_a(q, {"answer": "architecture"})
        assert check_answer(q, a) is True

    def test_wrong(self):
        q = make_q(QuestionType.GAP_FILL, {"correct": "architecture"})
        a = make_a(q, {"answer": "design"})
        assert check_answer(q, a) is False


# ── Matching ───────────────────────────────────────────────────────────────────

class TestMatching:
    ITEMS = ["Climate data is unreliable", "More research is needed", "Action is urgent"]

    def test_all_correct_canonical(self):
        correct = {item: letter for item, letter in zip(self.ITEMS, ["A", "B", "C"])}
        q = make_q(QuestionType.MATCHING, {"correct": correct}, {"items": self.ITEMS})
        student = {item: letter for item, letter in zip(self.ITEMS, ["A", "B", "C"])}
        a = make_a(q, {"answer": student})
        c, t = score_answer(q, a)
        assert t == 3
        assert c == 3

    def test_partial_credit_canonical(self):
        correct = {item: letter for item, letter in zip(self.ITEMS, ["A", "B", "C"])}
        q = make_q(QuestionType.MATCHING, {"correct": correct}, {"items": self.ITEMS})
        student = {item: letter for item, letter in zip(self.ITEMS, ["A", "X", "C"])}
        a = make_a(q, {"answer": student})
        c, t = score_answer(q, a)
        assert t == 3
        assert c == 2

    def test_legacy_answers_array(self):
        """Legacy seed: {"answers": ["A","B","C"]} paired with content.items"""
        q = make_q(
            QuestionType.MATCHING,
            {"answers": ["A", "B", "C"]},
            {"items": self.ITEMS},
        )
        student = {item: letter for item, letter in zip(self.ITEMS, ["A", "B", "C"])}
        a = make_a(q, {"answer": student})
        c, t = score_answer(q, a)
        assert t == 3
        assert c == 3

    def test_all_wrong(self):
        correct = {item: letter for item, letter in zip(self.ITEMS, ["A", "B", "C"])}
        q = make_q(QuestionType.MATCHING, {"correct": correct}, {"items": self.ITEMS})
        a = make_a(q, {"answer": {item: "X" for item in self.ITEMS}})
        c, t = score_answer(q, a)
        assert c == 0
        assert t == 3

    def test_no_student_answer(self):
        correct = {item: letter for item, letter in zip(self.ITEMS, ["A", "B", "C"])}
        q = make_q(QuestionType.MATCHING, {"correct": correct})
        a = make_a(q, {"answer": ""})
        c, t = score_answer(q, a)
        assert c == 0


# ── MultiSelect ────────────────────────────────────────────────────────────────

class TestMultiSelect:
    """Each multi_select Question holds one correct letter; 1 mark if that
    letter appears anywhere in the student's chosen list."""

    def test_correct_letter_in_list(self):
        q = make_q(QuestionType.MULTI_SELECT, {"correct": "B"})
        a = make_a(q, {"answer": ["A", "B"]})
        c, t = score_answer(q, a)
        assert t == 1
        assert c == 1

    def test_correct_letter_not_in_list(self):
        q = make_q(QuestionType.MULTI_SELECT, {"correct": "B"})
        a = make_a(q, {"answer": ["A", "C"]})
        c, t = score_answer(q, a)
        assert t == 1
        assert c == 0

    def test_empty_list(self):
        q = make_q(QuestionType.MULTI_SELECT, {"correct": "A"})
        a = make_a(q, {"answer": []})
        c, t = score_answer(q, a)
        assert c == 0

    def test_case_insensitive(self):
        q = make_q(QuestionType.MULTI_SELECT, {"correct": "A"})
        a = make_a(q, {"answer": ["a", "b"]})
        c, t = score_answer(q, a)
        assert c == 1


# ── score_section aggregation ──────────────────────────────────────────────────

class TestScoreSection:
    def test_aggregates_mcq(self):
        questions = [
            make_q(QuestionType.MCQ, {"correct": str(i)})
            for i in range(5)
        ]
        answers = [
            make_a(q, {"answer": str(i)})
            for i, q in enumerate(questions)
        ]
        c, t = score_section(questions, answers)
        assert c == 5
        assert t == 5

    def test_matching_subitems_counted(self):
        """A single matching Q with 5 pairs contributes 5 to the total count."""
        items = [f"item{i}" for i in range(5)]
        correct = {item: "A" for item in items}
        q = make_q(QuestionType.MATCHING, {"correct": correct}, {"items": items})
        # Student gets 3 right
        student = {item: ("A" if i < 3 else "B") for i, item in enumerate(items)}
        a = make_a(q, {"answer": student})
        c, t = score_section([q], [a])
        assert t == 5
        assert c == 3

    def test_essay_skipped(self):
        questions = [make_q(QuestionType.ESSAY, None)]
        answers = [make_a(questions[0], {"answer": "long essay text"})]
        c, t = score_section(questions, answers)
        assert c == 0
        assert t == 0

    def test_multi_section_aggregation(self):
        """Simulate 4 Listening parts (10 Q each) → correct aggregated to 40."""
        all_questions = []
        all_answers = []
        for part in range(4):
            for i in range(10):
                q = make_q(QuestionType.MCQ, {"correct": "X"})
                a = make_a(q, {"answer": "X"})
                all_questions.append(q)
                all_answers.append(a)
        c, t = score_section(all_questions, all_answers)
        assert t == 40
        assert c == 40


# ── Band conversion boundaries ─────────────────────────────────────────────────

class TestBandTables:
    @pytest.mark.parametrize("raw, expected_band", [
        (40, 9.0), (39, 8.5), (37, 8.0), (36, 7.5), (32, 7.0),
        (30, 6.5), (26, 6.0), (23, 5.5), (18, 5.0), (0, 0.0),
    ])
    def test_listening_band(self, raw, expected_band):
        assert correct_to_listening_band(raw) == expected_band

    @pytest.mark.parametrize("raw, expected_band", [
        (40, 9.0), (39, 8.5), (37, 8.0), (35, 7.5), (33, 7.0),
        (30, 6.5), (27, 6.0), (23, 5.5), (19, 5.0), (0, 0.0),
    ])
    def test_reading_band(self, raw, expected_band):
        assert correct_to_reading_band(raw) == expected_band

    def test_listening_40_is_band9(self):
        assert correct_to_listening_band(40) == 9.0

    def test_reading_40_is_band9(self):
        assert correct_to_reading_band(40) == 9.0
