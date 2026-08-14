"""Unit tests for compound completion structure helpers and scoring."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.models.question import QuestionType
from app.services.compound import (
    check_compound_group_completeness,
    extract_gap_ids,
    validate_compound_gap_content,
    validate_compound_structure,
)
from app.services.scoring import score_answer


def _table_structure(**overrides):
    """Canonical plain-cell table (with variant)."""
    base = {
        "variant": "table",
        "instruction_words": "ONE WORD AND/OR A NUMBER",
        "max_words_per_gap": 2,
        "headers": ["Name", "Location"],
        "rows": [
            [
                {
                    "variant": "plain",
                    "segments": [{"type": "text", "value": "Cafe"}],
                },
                {
                    "variant": "plain",
                    "segments": [{"type": "gap", "gap_id": "g1"}],
                },
            ],
            [
                {
                    "variant": "plain",
                    "segments": [{"type": "gap", "gap_id": "g2"}],
                },
                {
                    "variant": "plain",
                    "segments": [{"type": "text", "value": "City"}],
                },
            ],
        ],
    }
    base.update(overrides)
    return base


def _table_structure_with_bullets():
    """Mixed plain + bullets cells (Cambridge-style Other comments)."""
    return {
        "variant": "table",
        "instruction_words": "ONE WORD AND/OR A NUMBER",
        "max_words_per_gap": 2,
        "headers": ["Name", "Other comments"],
        "rows": [
            [
                {
                    "variant": "plain",
                    "segments": [{"type": "text", "value": "Paloma"}],
                },
                {
                    "variant": "bullets",
                    "bullets": [
                        {
                            "segments": [
                                {"type": "text", "value": "Quite expensive"}
                            ]
                        },
                        {
                            "segments": [
                                {"type": "text", "value": "The "},
                                {"type": "gap", "gap_id": "g1"},
                                {
                                    "type": "text",
                                    "value": " is a good place for a drink",
                                },
                            ]
                        },
                    ],
                },
            ],
            [
                {
                    "variant": "plain",
                    "segments": [{"type": "gap", "gap_id": "g2"}],
                },
                {
                    "variant": "plain",
                    "segments": [{"type": "text", "value": ""}],
                },
            ],
        ],
    }


def _table_structure_legacy():
    """Pre-segments table shape (type text|gap)."""
    return {
        "variant": "table",
        "instruction_words": "ONE WORD AND/OR A NUMBER",
        "max_words_per_gap": 2,
        "headers": ["Name", "Location"],
        "rows": [
            [
                {"type": "text", "value": "Cafe"},
                {"type": "gap", "gap_id": "g1"},
            ],
            [
                {"type": "gap", "gap_id": "g2"},
                {"type": "text", "value": "City"},
            ],
        ],
    }


def _notes_structure():
    """Canonical segments-shaped notes."""
    return {
        "variant": "notes",
        "instruction_words": "NO MORE THAN TWO WORDS",
        "max_words_per_gap": 2,
        "title": "Farm Tours",
        "sections": [
            {
                "heading": "Location",
                "items": [
                    {"segments": [{"type": "text", "value": "Address:"}]},
                    {
                        "segments": [
                            {"type": "gap", "gap_id": "g1"},
                            {"type": "text", "value": "Road"},
                        ]
                    },
                ],
            }
        ],
    }


def _notes_structure_legacy():
    return {
        "variant": "notes",
        "instruction_words": "NO MORE THAN TWO WORDS",
        "max_words_per_gap": 2,
        "title": "Farm Tours",
        "sections": [
            {
                "heading": "Location",
                "items": [
                    {"type": "text", "value": "Address:"},
                    {"type": "gap_line", "prefix": "", "gap_id": "g1", "suffix": "Road"},
                ],
            }
        ],
    }


def _form_structure():
    """Canonical segments-shaped form."""
    return {
        "variant": "form",
        "instruction_words": "ONE WORD ONLY",
        "max_words_per_gap": 1,
        "form_title": "VIDEO LIBRARY APPLICATION FORM",
        "fields": [
            {"type": "static", "label": "Surname", "value": "Jones"},
            {
                "type": "gap_line",
                "label": "Address",
                "segments": [
                    {"type": "text", "value": "72 "},
                    {"type": "gap", "gap_id": "g1"},
                    {"type": "text", "value": " Street"},
                ],
            },
        ],
    }


def _form_structure_legacy():
    return {
        "variant": "form",
        "instruction_words": "ONE WORD ONLY",
        "max_words_per_gap": 1,
        "form_title": "VIDEO LIBRARY APPLICATION FORM",
        "fields": [
            {"type": "static", "label": "Surname", "value": "Jones"},
            {
                "type": "gap",
                "label": "Address",
                "gap_id": "g1",
                "prefix": "72 ",
                "suffix": " Street",
            },
        ],
    }


def _summary_structure():
    return {
        "variant": "summary",
        "instruction_words": "ONE WORD ONLY",
        "max_words_per_gap": 1,
        "paragraphs": [
            {
                "segments": [
                    {"type": "text", "value": "The Kakapo is a "},
                    {"type": "gap", "gap_id": "g1"},
                    {"type": "text", "value": " parrot."},
                ]
            }
        ],
    }


class TestExtractGapIds:
    def test_table(self):
        assert extract_gap_ids(_table_structure()) == ["g1", "g2"]

    def test_table_mixed_cell(self):
        structure = _table_structure(
            rows=[
                [
                    {
                        "variant": "plain",
                        "segments": [
                            {"type": "text", "value": "At the top of a "},
                            {"type": "gap", "gap_id": "g1"},
                        ],
                    },
                    {
                        "variant": "plain",
                        "segments": [{"type": "text", "value": "City"}],
                    },
                ]
            ]
        )
        assert extract_gap_ids(structure) == ["g1"]

    def test_table_bullets(self):
        assert extract_gap_ids(_table_structure_with_bullets()) == ["g1", "g2"]

    def test_table_legacy(self):
        assert extract_gap_ids(_table_structure_legacy()) == ["g1", "g2"]

    def test_notes(self):
        assert extract_gap_ids(_notes_structure()) == ["g1"]

    def test_notes_legacy(self):
        assert extract_gap_ids(_notes_structure_legacy()) == ["g1"]

    def test_form(self):
        assert extract_gap_ids(_form_structure()) == ["g1"]

    def test_form_legacy(self):
        assert extract_gap_ids(_form_structure_legacy()) == ["g1"]

    def test_summary(self):
        assert extract_gap_ids(_summary_structure()) == ["g1"]

    def test_empty(self):
        assert extract_gap_ids(None) == []
        assert extract_gap_ids({}) == []


class TestValidateStructure:
    def test_table_ok(self):
        validate_compound_structure("table_completion", _table_structure())

    def test_table_mixed_cell_ok(self):
        structure = _table_structure(
            rows=[
                [
                    {
                        "variant": "plain",
                        "segments": [
                            {"type": "text", "value": "keen on "},
                            {"type": "gap", "gap_id": "g1"},
                        ],
                    },
                    {
                        "variant": "plain",
                        "segments": [{"type": "text", "value": "x"}],
                    },
                ]
            ]
        )
        validate_compound_structure("table_completion", structure)

    def test_table_bullets_ok(self):
        validate_compound_structure(
            "table_completion", _table_structure_with_bullets()
        )

    def test_table_bullets_empty_rejected(self):
        bad = _table_structure(
            headers=["A", "B"],
            rows=[
                [
                    {
                        "variant": "bullets",
                        "bullets": [],
                    },
                    {
                        "variant": "plain",
                        "segments": [{"type": "gap", "gap_id": "g1"}],
                    },
                ]
            ],
        )
        with pytest.raises(ValueError, match="non-empty bullets"):
            validate_compound_structure("table_completion", bad)

    def test_table_legacy_ok(self):
        validate_compound_structure("table_completion", _table_structure_legacy())

    def test_notes_ok(self):
        validate_compound_structure("note_completion", _notes_structure())

    def test_notes_legacy_ok(self):
        validate_compound_structure("note_completion", _notes_structure_legacy())

    def test_form_ok(self):
        validate_compound_structure("form_completion", _form_structure())

    def test_form_legacy_ok(self):
        validate_compound_structure("form_completion", _form_structure_legacy())

    def test_summary_ok(self):
        validate_compound_structure("summary_completion", _summary_structure())

    def test_wrong_variant(self):
        with pytest.raises(ValueError, match="variant"):
            validate_compound_structure("table_completion", _notes_structure())

    def test_missing_gaps(self):
        bad = _table_structure(
            rows=[
                [
                    {
                        "variant": "plain",
                        "segments": [{"type": "text", "value": "a"}],
                    },
                    {
                        "variant": "plain",
                        "segments": [{"type": "text", "value": "b"}],
                    },
                ]
            ]
        )
        with pytest.raises(ValueError, match="at least one gap"):
            validate_compound_structure("table_completion", bad)

    def test_duplicate_gap_ids(self):
        bad = _table_structure(
            rows=[
                [
                    {
                        "variant": "plain",
                        "segments": [{"type": "gap", "gap_id": "g1"}],
                    },
                    {
                        "variant": "plain",
                        "segments": [{"type": "gap", "gap_id": "g1"}],
                    },
                ],
            ]
        )
        with pytest.raises(ValueError, match="duplicate"):
            validate_compound_structure("table_completion", bad)


class TestGapContentValidation:
    def test_valid_gap(self):
        validate_compound_gap_content(
            "table_completion",
            _table_structure(),
            {"gap_id": "g1"},
        )

    def test_unknown_gap(self):
        with pytest.raises(ValueError, match="not present"):
            validate_compound_gap_content(
                "table_completion",
                _table_structure(),
                {"gap_id": "wrong"},
            )


class TestCompleteness:
    def test_missing_question(self):
        qs = [SimpleNamespace(content={"gap_id": "g1"})]
        errors = check_compound_group_completeness(
            "table_completion",
            _table_structure(),
            qs,
        )
        assert any("missing" in e for e in errors)

    def test_complete(self):
        qs = [
            SimpleNamespace(content={"gap_id": "g1"}),
            SimpleNamespace(content={"gap_id": "g2"}),
        ]
        assert check_compound_group_completeness(
            "table_completion",
            _table_structure(),
            qs,
        ) == []


def make_q(qtype, answer_key, content=None):
    return SimpleNamespace(
        id=uuid.uuid4(),
        order=1,
        question_type=qtype,
        answer_key=answer_key,
        content=content or {},
    )


def make_a(question, response):
    return SimpleNamespace(
        id=uuid.uuid4(),
        question_id=question.id,
        attempt_id=uuid.uuid4(),
        response=response,
        is_correct=None,
        score=None,
    )


class TestCompoundScoring:
    def test_correct(self):
        q = make_q(
            QuestionType.TABLE_COMPLETION,
            {"correct": ["Audley", "audley"], "max_words": 2},
            {"gap_id": "g1"},
        )
        a = make_a(q, {"answer": "Audley"})
        assert score_answer(q, a) == (1, 1)

    def test_wrong(self):
        q = make_q(
            QuestionType.NOTE_COMPLETION,
            {"correct": ["Audley"], "max_words": 2},
            {"gap_id": "g1"},
        )
        a = make_a(q, {"answer": "London"})
        assert score_answer(q, a) == (0, 1)

    def test_max_words_exceeded_wrong_answer(self):
        q = make_q(
            QuestionType.FORM_COMPLETION,
            {"correct": ["Audley"], "max_words": 1},
            {"gap_id": "g1"},
        )
        a = make_a(q, {"answer": "Audley Street"})
        assert score_answer(q, a) == (0, 1)

    def test_accepted_variant_longer_than_max_words(self):
        """Number words in answer_key must score even if max_words is tighter."""
        q = make_q(
            QuestionType.FORM_COMPLETION,
            {
                "correct": [
                    "115",
                    "a hundred fifteen",
                    "a hundred and fifteen",
                    "one hundred fifteen",
                    "one hundred and fifteen",
                ],
                "max_words": 2,
            },
            {"gap_id": "g1"},
        )
        for ans in (
            "115",
            "a hundred fifteen",
            "a hundred and fifteen",
            "one hundred fifteen",
            "one hundred and fifteen",
        ):
            a = make_a(q, {"answer": ans})
            assert score_answer(q, a) == (1, 1), ans

    def test_case_insensitive_default(self):
        q = make_q(
            QuestionType.SUMMARY_COMPLETION,
            {"correct": ["flightless"], "max_words": 1},
            {"gap_id": "g1"},
        )
        a = make_a(q, {"answer": "Flightless"})
        assert score_answer(q, a) == (1, 1)

    def test_case_sensitive(self):
        q = make_q(
            QuestionType.TABLE_COMPLETION,
            {"correct": ["Audley"], "case_sensitive": True, "max_words": 1},
            {"gap_id": "g1"},
        )
        a = make_a(q, {"answer": "audley"})
        assert score_answer(q, a) == (0, 1)
