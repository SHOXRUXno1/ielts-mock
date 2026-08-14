"""Pure-logic tests for the practice-mode branches of section_progress.

Verifies:

* ``ensure_progress_rows`` seeds exactly one row when ``present_types`` names a
  single skill (practice) and still seeds the canonical four when it's absent
  (full-mock back-compat).
* ``compute_ends_at`` honours ``override_minutes`` (practice per-part
  duration) over the default section-level duration.
* Speaking practice with no duration falls back to the safety hard cap.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.models.section import SectionType
from app.services.section_progress import (
    SPEAKING_HARD_CAP_MINUTES,
    compute_ends_at,
    ensure_progress_rows,
)


def _setting(section_type: str, duration_minutes: int | None):
    return SimpleNamespace(section_type=section_type, duration_minutes=duration_minutes)


class TestEnsureProgressRows:
    def test_default_seeds_all_four_types(self):
        rows = ensure_progress_rows(uuid4(), None)
        assert [r.section_type for r in rows] == [
            SectionType.LISTENING.value,
            SectionType.READING.value,
            SectionType.WRITING.value,
            SectionType.SPEAKING.value,
        ]

    def test_practice_scope_seeds_only_target(self):
        # Practice for Reading Passage 2 → single row for reading.
        rows = ensure_progress_rows(uuid4(), [SectionType.READING.value])
        assert len(rows) == 1
        assert rows[0].section_type == SectionType.READING.value
        assert rows[0].state == "not_started"

    def test_empty_present_types_falls_back_to_all(self):
        # Empty iterable is not "None"; caller most likely made a mistake — we
        # fall back to the canonical four rather than seeding zero.
        rows = ensure_progress_rows(uuid4(), [])
        assert len(rows) == 4

    def test_present_types_are_ordered_canonically(self):
        # Even if the caller lists Writing first, we always seed in TYPE_ORDER.
        rows = ensure_progress_rows(
            uuid4(),
            [SectionType.WRITING.value, SectionType.LISTENING.value],
        )
        assert [r.section_type for r in rows] == [
            SectionType.LISTENING.value,
            SectionType.WRITING.value,
        ]


class TestComputeEndsAtOverride:
    def _now(self):
        return datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def test_override_wins_over_section_default(self):
        now = self._now()
        settings = [_setting(SectionType.LISTENING.value, 30)]
        end = compute_ends_at(
            now,
            settings,
            SectionType.LISTENING.value,
            override_minutes=7,
        )
        assert end is not None
        assert (end - now).total_seconds() == 7 * 60

    def test_no_override_uses_section_default(self):
        now = self._now()
        settings = [_setting(SectionType.READING.value, 60)]
        end = compute_ends_at(now, settings, SectionType.READING.value)
        assert end is not None
        assert (end - now).total_seconds() == 60 * 60

    def test_none_override_falls_back_to_section_default(self):
        now = self._now()
        settings = [_setting(SectionType.WRITING.value, 60)]
        end = compute_ends_at(
            now,
            settings,
            SectionType.WRITING.value,
            override_minutes=None,
        )
        assert end is not None
        assert (end - now).total_seconds() == 60 * 60

    def test_single_section_listening_uses_full_budget(self):
        """Whole-section practice: override=None → TestSectionSettings duration."""
        now = self._now()
        settings = [_setting(SectionType.LISTENING.value, 30)]
        end = compute_ends_at(
            now,
            settings,
            SectionType.LISTENING.value,
            override_minutes=None,
        )
        assert end is not None
        assert (end - now).total_seconds() == 30 * 60

    def test_single_section_reading_uses_full_budget(self):
        now = self._now()
        settings = [_setting(SectionType.READING.value, 60)]
        end = compute_ends_at(
            now,
            settings,
            SectionType.READING.value,
            override_minutes=None,
        )
        assert end is not None
        assert (end - now).total_seconds() == 60 * 60

    def test_speaking_with_no_duration_uses_hard_cap(self):
        # Practice for Speaking Part 2 with no admin duration → safety cap.
        now = self._now()
        end = compute_ends_at(now, [], SectionType.SPEAKING.value)
        assert end is not None
        assert (end - now).total_seconds() == SPEAKING_HARD_CAP_MINUTES * 60

    def test_speaking_with_override_respects_override(self):
        now = self._now()
        end = compute_ends_at(
            now,
            [],
            SectionType.SPEAKING.value,
            override_minutes=3,
        )
        assert end is not None
        assert (end - now).total_seconds() == 3 * 60

    def test_untimed_section_without_override_returns_none(self):
        # Non-speaking section with no configured minutes → no deadline.
        assert compute_ends_at(self._now(), [], SectionType.READING.value) is None
