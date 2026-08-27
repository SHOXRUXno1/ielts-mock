"""Overall band is always the official 4-skill IELTS average.

Skipped skills count as 0. IELTS half-up rounding: .25 → .5, .75 → next whole.
"""

from types import SimpleNamespace

from app.models.attempt import AttemptStatus
from app.services.band_calc import (
    compute_overall_band,
    derive_scored_status,
    round_ielts_band,
)
from app.services.scoring import compute_writing_band


def _attempt(**bands: float | None) -> SimpleNamespace:
    return SimpleNamespace(
        listening_band=bands.get("listening"),
        reading_band=bands.get("reading"),
        writing_band=bands.get("writing"),
        speaking_band=bands.get("speaking"),
    )


class TestRoundIeltsBand:
    def test_quarter_rounds_up(self):
        assert round_ielts_band(6.25) == 6.5

    def test_three_quarter_rounds_up(self):
        assert round_ielts_band(6.75) == 7.0

    def test_exact_half(self):
        assert round_ielts_band(6.5) == 6.5

    def test_below_quarter(self):
        assert round_ielts_band(6.1) == 6.0

    def test_near_whole(self):
        assert round_ielts_band(6.9) == 7.0


class TestComputeOverallBand:
    def test_skipped_speaking_counts_as_zero(self):
        # (5 + 5 + 5 + 0) / 4 = 3.75 → 4.0
        assert compute_overall_band(
            _attempt(listening=5.0, reading=5.0, writing=5.0, speaking=None)
        ) == 4.0

    def test_explicit_zero_speaking_same_as_skip(self):
        assert compute_overall_band(
            _attempt(listening=5.0, reading=5.0, writing=5.0, speaking=0.0)
        ) == 4.0

    def test_two_skills_still_divide_by_four(self):
        # (7 + 6.5 + 0 + 0) / 4 = 3.375 → 3.5
        assert compute_overall_band(
            _attempt(listening=7.0, reading=6.5, writing=None, speaking=None)
        ) == 3.5

    def test_single_skill_still_divide_by_four(self):
        # (0 + 0 + 9 + 0) / 4 = 2.25 → 2.5
        assert compute_overall_band(
            _attempt(listening=None, reading=None, writing=9.0, speaking=None)
        ) == 2.5

    def test_includes_zero_attempted_section(self):
        # (7 + 6.5 + 0 + 0) / 4 = 3.375 → 3.5
        assert compute_overall_band(
            _attempt(listening=7.0, reading=6.5, writing=0.0, speaking=None)
        ) == 3.5

    def test_three_scored_skills_include_the_skip(self):
        # (7 + 7 + 6.5 + 0) / 4 = 5.125 → 5.0
        assert compute_overall_band(
            _attempt(listening=7.0, reading=7.0, writing=6.5, speaking=None)
        ) == 5.0

    def test_three_sections_quarter_case(self):
        # (6.0 + 6.5 + 6.5 + 0) / 4 = 4.75 → 5.0
        assert compute_overall_band(
            _attempt(listening=6.0, reading=6.5, writing=6.5, speaking=None)
        ) == 5.0

    def test_four_sections_average(self):
        # (7 + 7 + 6.5 + 6.5) / 4 = 6.75 → 7.0
        assert compute_overall_band(
            _attempt(listening=7.0, reading=7.0, writing=6.5, speaking=6.5)
        ) == 7.0

    def test_all_missing(self):
        assert compute_overall_band(_attempt()) is None


class TestDeriveScoredStatus:
    def test_without_speaking_is_auto(self):
        assert (
            derive_scored_status(_attempt(listening=7.0, reading=6.0, writing=5.0, speaking=None))
            == AttemptStatus.AUTO_SCORED
        )

    def test_with_speaking_is_fully(self):
        assert (
            derive_scored_status(_attempt(listening=7.0, reading=6.0, writing=5.0, speaking=6.5))
            == AttemptStatus.FULLY_SCORED
        )

    def test_zero_speaking_is_fully(self):
        # 0.0 speaking = attempted but low score, still counts as fully scored
        assert (
            derive_scored_status(_attempt(listening=7.0, reading=6.0, writing=5.0, speaking=0.0))
            == AttemptStatus.FULLY_SCORED
        )

    def test_two_lrw_missing_is_partial(self):
        assert (
            derive_scored_status(_attempt(listening=7.0, reading=None, writing=None, speaking=None))
            == AttemptStatus.PARTIAL
        )

    def test_all_lrw_missing_is_partial(self):
        assert (
            derive_scored_status(_attempt(listening=None, reading=None, writing=None, speaking=None))
            == AttemptStatus.PARTIAL
        )

    def test_one_lrw_missing_is_auto(self):
        assert (
            derive_scored_status(_attempt(listening=7.0, reading=6.0, writing=None, speaking=None))
            == AttemptStatus.AUTO_SCORED
        )


class TestIncompleteWritingOverall:
    """Writing overall requires both tasks — never invent 0.0."""

    def test_task1_only_is_none(self):
        assert compute_writing_band(9.0, None) is None

    def test_task2_only_is_none(self):
        assert compute_writing_band(None, 8.0) is None

    def test_both_tasks(self):
        # (9*1 + 8*2) / 3 = 8.333… → 8.5
        assert compute_writing_band(9.0, 8.0) == 8.5
