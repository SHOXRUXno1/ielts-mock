"""Pure-logic unit tests for the single-part practice mode.

These cover the deterministic slice of ``app.services.practice_parts`` that
doesn't need a database — the proportional default-duration policy and the
proportional-fallback helper used by ``compute_ends_at``. The DB-heavy paths
(enumerate_units / find_unit) are exercised end-to-end through the API tests
that already boot a real session.
"""

from types import SimpleNamespace

from app.models.section import SectionType
from app.services.practice_parts import (
    SPEAKING_PART_MINUTES,
    WRITING_TASK_DEFAULT,
    WRITING_TASK_MINUTES,
    _proportional_from_settings,
    default_duration,
)


class TestDefaultDuration:
    def test_listening_splits_evenly(self):
        # 30 min / 4 parts = 7.5 → 8 (round-half-to-even lands on 8).
        assert default_duration(SectionType.LISTENING.value, 1, 30, 4) == 8

    def test_reading_splits_evenly(self):
        # 60 min / 3 passages = 20 min per passage.
        for passage in (1, 2, 3):
            assert default_duration(SectionType.READING.value, passage, 60, 3) == 20

    def test_listening_never_below_one_minute(self):
        # Tiny section with many parts — floor at 1 minute.
        assert default_duration(SectionType.LISTENING.value, 1, 1, 4) == 1

    def test_writing_task1_fixed(self):
        assert default_duration(SectionType.WRITING.value, 1, 60, 2) == WRITING_TASK_MINUTES[1]

    def test_writing_task2_fixed(self):
        assert default_duration(SectionType.WRITING.value, 2, 60, 2) == WRITING_TASK_MINUTES[2]

    def test_writing_unknown_task_falls_back(self):
        assert default_duration(SectionType.WRITING.value, 5, 60, 2) == WRITING_TASK_DEFAULT

    def test_speaking_returns_none(self):
        # Speaking is AI-paced — no hard timer, no proportional split.
        for part in (1, 2, 3):
            assert default_duration(SectionType.SPEAKING.value, part, 15, 3) is None

    def test_missing_section_minutes_returns_none(self):
        assert default_duration(SectionType.LISTENING.value, 1, None, 4) is None

    def test_zero_part_count_returns_none(self):
        assert default_duration(SectionType.LISTENING.value, 1, 30, 0) is None


class TestProportionalFromSettings:
    def _rows(self, **minutes: int):
        return [
            SimpleNamespace(section_type=stype, duration_minutes=mins)
            for stype, mins in minutes.items()
        ]

    def test_uses_matching_section_row(self):
        rows = self._rows(listening=40, reading=60)
        assert (
            _proportional_from_settings(rows, SectionType.LISTENING.value, 1, 4)
            == 10
        )

    def test_returns_none_when_section_absent(self):
        # No matching row → default_duration receives ``None`` and bails.
        rows = self._rows(reading=60)
        assert (
            _proportional_from_settings(rows, SectionType.LISTENING.value, 1, 4)
            is None
        )

    def test_writing_ignores_section_minutes(self):
        # Writing duration is fixed IELTS convention.
        rows = self._rows(writing=90)
        assert (
            _proportional_from_settings(rows, SectionType.WRITING.value, 2, 2)
            == WRITING_TASK_MINUTES[2]
        )

    def test_speaking_stays_none(self):
        rows = self._rows(speaking=15)
        assert (
            _proportional_from_settings(rows, SectionType.SPEAKING.value, 1, 3)
            is None
        )


def test_speaking_defaults_are_declared():
    # Regression: state-machine safety cap references these values.
    assert set(SPEAKING_PART_MINUTES.keys()) == {1, 2, 3}
    assert all(v > 0 for v in SPEAKING_PART_MINUTES.values())
