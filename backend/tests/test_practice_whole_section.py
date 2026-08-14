"""Pure-logic tests for whole-section practice units."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from app.models.attempt import AttemptMode, PRACTICE_MODES
from app.models.section import SectionType
from app.services.practice_parts import (
    PracticeSectionUnit,
    _SECTION_LABELS,
    _scoring_slots,
)


class TestPracticeModes:
    def test_practice_modes_includes_part_and_section(self):
        assert AttemptMode.SINGLE_PART.value in PRACTICE_MODES
        assert AttemptMode.SINGLE_SECTION.value in PRACTICE_MODES
        assert AttemptMode.FULL_MOCK.value not in PRACTICE_MODES


class TestSectionLabels:
    def test_all_skills_have_full_labels(self):
        for stype in SectionType:
            assert stype.value in _SECTION_LABELS
            assert _SECTION_LABELS[stype.value].startswith("Full ")


class TestPracticeSectionUnitShape:
    def test_dataclass_fields(self):
        unit = PracticeSectionUnit(
            section_type="listening",
            label="Full Listening",
            part_count=4,
            question_count=40,
            duration_minutes=30,
            is_enabled=True,
        )
        assert unit.section_type == "listening"
        assert unit.part_count == 4
        assert unit.question_count == 40
        assert unit.duration_minutes == 30


class TestScoringSlotsAggregation:
    def test_sums_slots_across_questions(self):
        q1 = SimpleNamespace(
            question_type="mcq",
            content={"options": ["A", "B"]},
            answer_key={"correct": "A"},
        )
        # scoring_slots_for_question typically returns >= 1 for mcq
        total = _scoring_slots([q1, q1])
        assert total >= 2


def test_single_section_duration_policy():
    """Whole-section practice uses TestSectionSettings (override=None).

    Documented contract: callers pass duration_override_minutes=None so
    compute_ends_at falls back to the section-level budget.
    """
    from datetime import datetime, timezone

    from app.services.section_progress import compute_ends_at

    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    settings = [
        SimpleNamespace(section_type="listening", duration_minutes=30),
    ]
    end = compute_ends_at(
        now,
        settings,
        "listening",
        override_minutes=None,
    )
    assert end is not None
    assert (end - now).total_seconds() == 30 * 60


def test_attempt_mode_single_section_value():
    assert AttemptMode.SINGLE_SECTION.value == "single_section"
    # UUID helper kept so the file exercises uuid imports used elsewhere.
    assert uuid4() is not None
