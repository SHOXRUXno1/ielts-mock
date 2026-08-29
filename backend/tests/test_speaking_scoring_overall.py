"""Tests for server-side overall_band recomputation in speaking scoring."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.llm import (
    SPEAKING_BAND_BOOST,
    _apply_speaking_boost,
    _coerce_speaking_criteria_to_int,
    _recompute_overall_band,
    evaluate_speaking,
    evaluate_speaking_dialog,
)


def _score_result(
    fc: float,
    lr: float,
    gr: float,
    pr: float,
    overall: float,
) -> dict:
    criterion = lambda band: {"band": band, "feedback": "ok"}
    return {
        "fluency_coherence": criterion(fc),
        "lexical_resource": criterion(lr),
        "grammatical_range": criterion(gr),
        "pronunciation": criterion(pr),
        "overall_band": overall,
        "strengths": [],
        "improvements": [],
        "corrections": [],
        "example_phrases": [],
    }


class TestRecomputeOverallBand:
    def test_recompute_overall_rounds_to_half(self):
        result = _score_result(6.0, 6.0, 7.0, 7.0, 8.0)
        updated = _recompute_overall_band(result)
        assert updated["overall_band"] == 6.5

    def test_recompute_overall_equal(self):
        result = _score_result(5.5, 5.5, 5.5, 5.5, 6.0)
        updated = _recompute_overall_band(result)
        assert updated["overall_band"] == 5.5


class TestCoerceSpeakingCriteriaToInt:
    """IELTS: individual Speaking criteria must be whole bands 0-9."""

    def test_rounds_half_bands(self):
        # IELTS half-up rounding: 6.5 -> 7, 7.5 -> 8, 8.6 -> 9.
        result = _score_result(6.5, 7.4, 7.5, 8.6, 9.0)
        out = _coerce_speaking_criteria_to_int(result)
        assert out["fluency_coherence"]["band"] == 7
        assert out["lexical_resource"]["band"] == 7
        assert out["grammatical_range"]["band"] == 8
        assert out["pronunciation"]["band"] == 9

    def test_integers_unchanged(self):
        result = _score_result(7, 6.0, 8, 5, 6.5)
        out = _coerce_speaking_criteria_to_int(result)
        assert out["fluency_coherence"]["band"] == 7
        assert out["lexical_resource"]["band"] == 6
        assert out["grammatical_range"]["band"] == 8
        assert out["pronunciation"]["band"] == 5

    def test_clamps_out_of_range(self):
        result = _score_result(9.7, -1.2, 10, 0, 5.0)
        out = _coerce_speaking_criteria_to_int(result)
        assert out["fluency_coherence"]["band"] == 9
        assert out["lexical_resource"]["band"] == 0
        assert out["grammatical_range"]["band"] == 9
        assert out["pronunciation"]["band"] == 0

    def test_non_numeric_band_skipped(self):
        result = {
            "fluency_coherence": {"band": "n/a", "feedback": "bad"},
            "lexical_resource": {"band": 6.5, "feedback": "ok"},
            "grammatical_range": {"band": 7, "feedback": "ok"},
            "pronunciation": {"band": 7, "feedback": "ok"},
            "overall_band": 7.0,
        }
        out = _coerce_speaking_criteria_to_int(result)
        assert out["fluency_coherence"]["band"] == "n/a"
        assert out["lexical_resource"]["band"] == 7  # half-up 6.5 -> 7


class TestApplySpeakingBoost:
    """Post-processing boost lifts each Speaking criterion by SPEAKING_BAND_BOOST."""

    def test_boost_is_configured_to_1_5(self):
        # If someone tunes it, both the code branch AND these tests will move.
        assert SPEAKING_BAND_BOOST == 1.5

    def test_lifts_each_criterion(self):
        result = _score_result(5, 6, 4, 7, 5.5)
        _apply_speaking_boost(result)
        # 5+1.5=6.5→7, 6+1.5=7.5→8, 4+1.5=5.5→6, 7+1.5=8.5→9
        assert result["fluency_coherence"]["band"] == 7
        assert result["lexical_resource"]["band"] == 8
        assert result["grammatical_range"]["band"] == 6
        assert result["pronunciation"]["band"] == 9

    def test_clamps_at_9(self):
        # 8 + 1.5 = 9.5 → clamp to 9, not overflow
        result = _score_result(8, 9, 8, 9, 8.5)
        _apply_speaking_boost(result)
        for key in ("fluency_coherence", "lexical_resource",
                    "grammatical_range", "pronunciation"):
            assert result[key]["band"] == 9

    def test_zero_stays_zero_then_boosted(self):
        # Boost applies to whatever coerce produced; the "candidate said
        # nothing" case is handled by hardcoded tier 0 in speaking_examiner,
        # never reaching this helper.
        result = _score_result(0, 0, 0, 0, 0.0)
        _apply_speaking_boost(result)
        # 0 + 1.5 = 1.5 half-up → 2
        for key in ("fluency_coherence", "lexical_resource",
                    "grammatical_range", "pronunciation"):
            assert result[key]["band"] == 2

    def test_missing_band_key_is_skipped(self):
        result = {
            "fluency_coherence": {"band": None, "feedback": ""},
            "lexical_resource": {"band": 6, "feedback": ""},
        }
        # Must not raise even without all criteria present.
        _apply_speaking_boost(result)
        assert result["fluency_coherence"]["band"] is None
        assert result["lexical_resource"]["band"] == 8

    def test_non_numeric_band_is_skipped(self):
        result = _score_result(6, 5, 7, 6, 6.0)
        result["fluency_coherence"]["band"] = "n/a"
        _apply_speaking_boost(result)
        assert result["fluency_coherence"]["band"] == "n/a"
        assert result["lexical_resource"]["band"] == 7  # 5+1.5=6.5→7


class TestEvaluateSpeakingDialogOverall:
    @pytest.mark.asyncio
    @patch("app.services.llm._call_gemini", new_callable=AsyncMock)
    async def test_evaluate_speaking_dialog_recomputes_overall(self, mock_gemini):
        mock_gemini.return_value = _score_result(6.0, 6.0, 7.0, 7.0, 8.0)

        result = await evaluate_speaking_dialog(
            [
                {"role": "examiner", "text": "Tell me about your hometown."},
                {"role": "candidate", "text": "I live in a small city near the mountains."},
            ],
        )

        # +1.5 boost: 6→8, 6→8, 7→9 (7+1.5=8.5 half-up), 7→9 → avg 8.5
        assert result["overall_band"] == 8.5
        assert result["transcript"] == "I live in a small city near the mountains."

    @pytest.mark.asyncio
    @patch("app.services.llm._call_gemini", new_callable=AsyncMock)
    async def test_evaluate_speaking_dialog_coerces_half_band_criteria(self, mock_gemini):
        # coerce: 6.5→7, 6.5→7, 7.0→7, 7.0→7
        # +1.5 boost:  7→8+, 7→8+, 7→8+, 7→8+ (7+1.5=8.5 half-up → 9)
        # overall = (9+9+9+9)/4 = 9.0
        mock_gemini.return_value = _score_result(6.5, 6.5, 7.0, 7.0, 8.0)

        result = await evaluate_speaking_dialog(
            [
                {"role": "examiner", "text": "What do you do?"},
                {"role": "candidate", "text": "I work as a teacher in a local school."},
            ],
        )

        assert result["fluency_coherence"]["band"] == 9
        assert result["lexical_resource"]["band"] == 9
        assert result["grammatical_range"]["band"] == 9
        assert result["pronunciation"]["band"] == 9
        assert result["overall_band"] == 9.0


class TestEvaluateSpeaking:
    @pytest.mark.asyncio
    @patch("app.services.llm._call_gemini", new_callable=AsyncMock)
    async def test_evaluate_speaking_coerces_and_recomputes(self, mock_gemini):
        # Gemini returns half-bands and a lying overall; backend must fix both.
        mock_gemini.return_value = _score_result(6.5, 7.4, 7.0, 6.0, 9.0)

        result = await evaluate_speaking(
            "I enjoy reading books in my free time.",
            questions=["What do you do in your free time?"],
        )

        # coerce (half-up): 6.5→7, 7.4→7, 7.0→7, 6.0→6
        # +1.5 boost:       7→9,  7→9,  7→9,  6→8 (6+1.5=7.5 half-up → 8)
        # overall = (9+9+9+8)/4 = 8.75 → 9.0 (round_ielts_band half-up)
        assert result["fluency_coherence"]["band"] == 9
        assert result["lexical_resource"]["band"] == 9
        assert result["grammatical_range"]["band"] == 9
        assert result["pronunciation"]["band"] == 8
        assert result["overall_band"] == 9.0
        assert result["transcript"] == "I enjoy reading books in my free time."
