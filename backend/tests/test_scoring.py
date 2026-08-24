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
    compute_writing_band,
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


class TestMatchingOneItemPerRow:
    """The shape the editor actually writes: a row per item, keyed by a letter.

    "What reason prevented each member from joining?" becomes one question per
    member — content {"stem": "Gen"} against a key of "A" — rather than one
    question holding every pair. Every question in the bank is written this way,
    and none of them had ever been marked correct: the pair branch found no
    pairs to walk and scored zero, so a candidate who picked A for a question
    whose answer was A was still told she was wrong.
    """

    def test_the_right_letter_earns_the_mark(self):
        q = make_q(QuestionType.MATCHING, {"correct": "A"}, {"stem": "Gen"})
        a = make_a(q, {"answer": "A"})
        assert score_answer(q, a) == (1, 1)
        assert a.is_correct is True
        assert a.score == 1.0

    def test_the_wrong_letter_earns_nothing(self):
        q = make_q(QuestionType.MATCHING, {"correct": "A"}, {"stem": "Gen"})
        a = make_a(q, {"answer": "C"})
        assert score_answer(q, a) == (0, 1)
        assert a.is_correct is False

    def test_case_and_padding_do_not_decide_it(self):
        q = make_q(QuestionType.MATCHING, {"correct": "A"}, {"stem": "Gen"})
        a = make_a(q, {"answer": " a "})
        assert score_answer(q, a) == (1, 1)

    def test_silence_is_not_an_answer(self):
        q = make_q(QuestionType.MATCHING, {"correct": "A"}, {"stem": "Gen"})
        a = make_a(q, {"answer": ""})
        assert score_answer(q, a) == (0, 1)
        assert a.is_correct is False

    def test_a_missing_key_never_reads_as_correct(self):
        """An empty key and an empty answer are both "", which must not match."""
        q = make_q(QuestionType.MATCHING, {}, {"stem": "Gen"})
        a = make_a(q, {"answer": ""})
        assert score_answer(q, a) == (0, 1)
        assert a.is_correct is False

    def test_it_is_worth_one_mark_when_unanswered(self):
        """Four such rows are four marks, not four questions worth one between them."""
        questions = [
            make_q(QuestionType.MATCHING, {"correct": letter}, {"stem": stem})
            for stem, letter in [("Gen", "A"), ("James", "C"), ("Leo", "B"), ("Mark", "C")]
        ]
        answers = [make_a(questions[0], {"answer": "A"})]
        c, t = score_section(questions, answers)
        assert (c, t) == (1, 4)


# ── MultiSelect ────────────────────────────────────────────────────────────────

class TestMultiSelect:
    """Scalar correct (legacy pair row): 1 mark if letter is in student list.
    List correct: N marks with partial credit per hit."""

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

    def test_list_full_match(self):
        q = make_q(
            QuestionType.MULTI_SELECT,
            {"correct": ["A", "C"]},
            {"options": ["alpha", "bravo", "charlie", "delta"]},
        )
        a = make_a(q, {"answer": ["A", "C"]})
        c, t = score_answer(q, a)
        assert (c, t) == (2, 2)
        assert a.is_correct is True

    def test_list_partial_credit(self):
        q = make_q(
            QuestionType.MULTI_SELECT,
            {"correct": ["A", "C"]},
            {"options": ["alpha", "bravo", "charlie", "delta"]},
        )
        a = make_a(q, {"answer": ["A", "B"]})
        c, t = score_answer(q, a)
        assert (c, t) == (1, 2)
        assert a.score == 0.5
        # is_correct is all-or-nothing, so the earned mark only shows in score.
        # Reports must read score, not is_correct, or the mark disappears.
        assert a.is_correct is False

    def test_list_none_correct(self):
        q = make_q(QuestionType.MULTI_SELECT, {"correct": ["A", "C"]})
        a = make_a(q, {"answer": ["B", "D"]})
        c, t = score_answer(q, a)
        assert (c, t) == (0, 2)

    def test_list_letter_matches_option_text(self):
        q = make_q(
            QuestionType.MULTI_SELECT,
            {"correct": ["alpha", "charlie"]},
            {"options": ["alpha", "bravo", "charlie", "delta"]},
        )
        a = make_a(q, {"answer": ["A", "C"]})
        c, t = score_answer(q, a)
        assert (c, t) == (2, 2)

    def test_scoring_slots(self):
        from app.services.scoring import scoring_slots_for_question

        assert scoring_slots_for_question(
            make_q(QuestionType.MULTI_SELECT, {"correct": ["A", "C"]})
        ) == 2
        assert scoring_slots_for_question(
            make_q(QuestionType.MULTI_SELECT, {"correct": "B"})
        ) == 1
        assert scoring_slots_for_question(
            make_q(QuestionType.MULTI_SELECT, None, {"choose_n": 2})
        ) == 2
        assert scoring_slots_for_question(make_q(QuestionType.MCQ, {"correct": "A"})) == 1


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

    def test_unanswered_count_toward_total(self):
        """Missing answers must not inflate the score (e.g. orphan gaps)."""
        questions = [
            make_q(QuestionType.MCQ, {"correct": "A"}),
            make_q(QuestionType.NOTE_COMPLETION, {"correct": ["gates"], "max_words": 1}),
            make_q(QuestionType.NOTE_COMPLETION, {"correct": ["clamp"], "max_words": 1}),
        ]
        answers = [make_a(questions[0], {"answer": "A"})]
        c, t = score_section(questions, answers)
        assert c == 1
        assert t == 3


# ── Band conversion boundaries ─────────────────────────────────────────────────

class TestBandTables:
    @pytest.mark.parametrize("raw, expected_band", [
        (40, 9.0), (39, 9.0), (38, 8.5), (37, 8.5),
        (36, 8.0), (35, 8.0), (34, 7.5), (32, 7.5),
        (31, 7.0), (30, 7.0), (29, 6.5), (26, 6.5),
        (25, 6.0), (23, 6.0), (22, 5.5), (18, 5.5),
        (17, 5.0), (16, 5.0), (15, 4.5), (13, 4.5),
        (12, 4.0), (11, 4.0), (10, 3.5), (8, 3.5),
        (7, 3.0), (6, 3.0), (5, 2.5), (4, 2.5),
        (3, 2.0), (2, 2.0), (1, 1.0), (0, 0.0),
    ])
    def test_listening_band(self, raw, expected_band):
        assert correct_to_listening_band(raw) == expected_band

    @pytest.mark.parametrize("raw, expected_band", [
        (40, 9.0), (39, 9.0), (38, 8.5), (37, 8.5),
        (36, 8.0), (35, 8.0), (34, 7.5), (33, 7.5),
        (32, 7.0), (30, 7.0), (29, 6.5), (27, 6.5),
        (26, 6.0), (23, 6.0), (22, 5.5), (19, 5.5),
        (18, 5.0), (15, 5.0), (14, 4.5), (13, 4.5),
        (12, 4.0), (10, 4.0), (9, 3.5), (8, 3.5),
        (7, 3.0), (6, 3.0), (5, 2.5), (4, 2.5),
        (3, 2.0), (2, 1.0), (1, 1.0), (0, 0.0),
    ])
    def test_reading_band(self, raw, expected_band):
        assert correct_to_reading_band(raw) == expected_band


class TestComputeWritingBand:
    def test_weighted_formula(self):
        # (6.0*1 + 7.0*2) / 3 = 6.666... → round to nearest 0.5 → 6.5
        assert compute_writing_band(6.0, 7.0) == 6.5

    def test_equal_bands(self):
        assert compute_writing_band(7.0, 7.0) == 7.0

    def test_missing_task1(self):
        assert compute_writing_band(None, 7.0) is None

    def test_missing_task2(self):
        assert compute_writing_band(6.0, None) is None

    def test_both_missing(self):
        assert compute_writing_band(None, None) is None

    def test_rounds_to_half(self):
        # (5.0*1 + 6.5*2) / 3 = 6.0 exactly
        assert compute_writing_band(5.0, 6.5) == 6.0


class TestAssignGroupsSlotNumbers:
    """Section-wide Q numbers when each group reuses local order 1..n."""

    def test_passage2_three_groups(self):
        from app.services.scoring import assign_groups_slot_numbers

        g1_qs = [
            SimpleNamespace(
                id=f"g1q{i}",
                order=i,
                question_type=QuestionType.MATCHING_INFORMATION,
                content={},
                answer_key={"correct": "A"},
            )
            for i in range(1, 6)
        ]
        g2_qs = [
            SimpleNamespace(
                id=f"g2q{i}",
                order=i,
                question_type=QuestionType.MATCHING_FEATURES,
                content={},
                answer_key={"correct": "A"},
            )
            for i in range(1, 6)
        ]
        g3_qs = [
            SimpleNamespace(
                id=f"g3q{i}",
                order=i,
                question_type=QuestionType.SUMMARY_COMPLETION,
                content={},
                answer_key={"correct": "word"},
            )
            for i in range(1, 4)
        ]
        groups = [
            SimpleNamespace(id="g1", order=1, questions=g1_qs),
            SimpleNamespace(id="g2", order=2, questions=g2_qs),
            SimpleNamespace(id="g3", order=3, questions=g3_qs),
        ]
        # Passage 2 starts at Q14 → base_offset 13
        ranges = assign_groups_slot_numbers(groups, base_offset=13)
        assert ranges["g1q1"] == (14, 14)
        assert ranges["g1q5"] == (18, 18)
        assert ranges["g2q1"] == (19, 19)  # not 18!
        assert ranges["g2q5"] == (23, 23)
        assert ranges["g3q1"] == (24, 24)
        assert ranges["g3q3"] == (26, 26)

    def test_multi_select_spans_slots(self):
        from app.services.scoring import assign_groups_slot_numbers

        g1 = SimpleNamespace(
            id="g1",
            order=1,
            questions=[
                SimpleNamespace(
                    id="ms1",
                    order=1,
                    question_type=QuestionType.MULTI_SELECT,
                    content={"choose_n": 2},
                    answer_key={"correct": ["A", "B"]},
                ),
            ],
        )
        g2 = SimpleNamespace(
            id="g2",
            order=2,
            questions=[
                SimpleNamespace(
                    id="mcq1",
                    order=1,
                    question_type=QuestionType.MCQ,
                    content={},
                    answer_key={"correct": "A"},
                ),
            ],
        )
        ranges = assign_groups_slot_numbers([g1, g2], base_offset=0)
        assert ranges["ms1"] == (1, 2)
        assert ranges["mcq1"] == (3, 3)
