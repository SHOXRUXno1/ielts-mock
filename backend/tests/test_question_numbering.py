"""Unit tests for IELTS question numbering (computed offsets + group-local order)."""

from types import SimpleNamespace

from app.models.question import QuestionType
from app.services.question_numbering import (
    annotate_question_numbers,
    compute_question_number,
    compute_section_offset,
    question_numbers_for_section,
    question_numbers_for_test,
)


def _q(qid, order, qtype=QuestionType.MCQ, choose_n=None, correct=None):
    content = {}
    if choose_n is not None:
        content["choose_n"] = choose_n
    answer_key = {"correct": correct} if correct is not None else {"correct": "A"}
    return SimpleNamespace(
        id=qid,
        order=order,
        question_type=qtype,
        content=content,
        answer_key=answer_key,
    )


def _g(gid, order, questions, qtype=None):
    return SimpleNamespace(
        id=gid,
        order=order,
        question_type=qtype,
        questions=questions,
    )


def _sec(sid, stype, order, groups, questions=None):
    return SimpleNamespace(
        id=sid,
        type=stype,
        order=order,
        question_groups=groups,
        questions=questions if questions is not None else [
            q for g in groups for q in g.questions
        ],
    )


class TestComputeSectionOffset:
    def test_first_section_starts_at_1(self):
        s = _sec("s1", "reading", 10, [])
        assert compute_section_offset(s, []) == 1

    def test_second_passage_after_13_slots(self):
        p1_qs = [_q(f"q{i}", i) for i in range(1, 14)]
        p1 = _sec("s1", "reading", 10, [_g("g1", 1, p1_qs)])
        p2 = _sec("s2", "reading", 11, [])
        assert compute_section_offset(p2, [p1]) == 14

    def test_nonstandard_cambridge_split(self):
        """cambridge-ielts-1: 9 + 13 + 8 — Passage 2 starts at Q10."""
        p1 = _sec(
            "s1",
            "reading",
            5,
            [_g("g1", 1, [_q(f"q{i}", i) for i in range(1, 10)])],
        )
        p2 = _sec("s2", "reading", 6, [])
        assert compute_section_offset(p2, [p1]) == 10


class TestQuestionNumbersForSection:
    def test_passage3_three_groups_after_26(self):
        """Standard Passage 3 (offset 26) with group-local orders 1..N."""
        g1 = _g("g1", 1, [_q(f"g1q{i}", i) for i in range(1, 5)])  # 4
        g2 = _g("g2", 2, [_q(f"g2q{i}", i) for i in range(1, 6)])  # 5
        g3 = _g("g3", 3, [_q(f"g3q{i}", i) for i in range(1, 6)])  # 5
        section = _sec("s3", "reading", 12, [g1, g2, g3])
        prior = [
            _sec("s1", "reading", 10, [_g("pg1", 1, [_q(f"p1q{i}", i) for i in range(1, 14)])]),
            _sec("s2", "reading", 11, [_g("pg2", 1, [_q(f"p2q{i}", i) for i in range(1, 14)])]),
        ]
        ranges = question_numbers_for_section(section, prior)
        assert ranges["g1q1"] == (27, 27)
        assert ranges["g1q4"] == (30, 30)
        assert ranges["g2q1"] == (31, 31)
        assert ranges["g2q5"] == (35, 35)
        assert ranges["g3q1"] == (36, 36)
        assert ranges["g3q5"] == (40, 40)

    def test_multi_select_spans(self):
        g1 = _g(
            "g1",
            1,
            [
                _q(
                    "ms1",
                    1,
                    qtype=QuestionType.MULTI_SELECT,
                    choose_n=2,
                    correct=["A", "B"],
                )
            ],
        )
        g2 = _g("g2", 2, [_q("mcq1", 1)])
        section = _sec("s1", "listening", 2, [g1, g2])
        # Prior: 10 slots
        prior = [
            _sec("s0", "listening", 1, [_g("pg", 1, [_q(f"q{i}", i) for i in range(1, 11)])])
        ]
        ranges = question_numbers_for_section(section, prior)
        assert ranges["ms1"] == (11, 12)
        assert ranges["mcq1"] == (13, 13)


class TestComputeQuestionNumber:
    def test_wrapper_matches_bulk(self):
        g1 = _g("g1", 1, [_q("a", 1), _q("b", 2)])
        g2 = _g("g2", 2, [_q("c", 1)])
        section = _sec("s1", "reading", 10, [g1, g2])
        test = SimpleNamespace(sections=[section])
        q = g2.questions[0]
        q.section = section
        q.group = g2
        assert compute_question_number(q, test) == 3


class TestAnnotate:
    def test_sets_transient_attrs(self):
        g1 = _g("g1", 1, [_q("a", 1), _q("b", 2)])
        section = _sec("s1", "reading", 10, [g1])
        test = SimpleNamespace(sections=[section])
        annotate_question_numbers(test)
        assert g1.questions[0].computed_number == 1
        assert g1.questions[0].computed_number_end is None
        assert g1.questions[1].computed_number == 2


class TestGroupScopedOrderSemantics:
    """Regression: order allocation is per-group (Fix 1 already in API)."""

    def test_second_group_orders_restart_at_1_in_numbering(self):
        # After renumber migration, both groups have order 1..N locally.
        g1 = _g("g1", 1, [_q(f"g1q{i}", i) for i in range(1, 5)])
        g2 = _g("g2", 2, [_q(f"g2q{i}", i) for i in range(1, 6)])
        section = _sec("s1", "reading", 12, [g1, g2])
        prior_slots = 26  # standard P3
        ranges = question_numbers_for_section(
            section,
            [
                _sec(
                    "p1",
                    "reading",
                    10,
                    [_g("x", 1, [_q(f"x{i}", i) for i in range(1, 14)])],
                ),
                _sec(
                    "p2",
                    "reading",
                    11,
                    [_g("y", 1, [_q(f"y{i}", i) for i in range(1, 14)])],
                ),
            ],
        )
        assert g2.questions[0].order == 1  # group-local
        assert ranges["g2q1"] == (prior_slots + 4 + 1, prior_slots + 4 + 1)  # Q31
