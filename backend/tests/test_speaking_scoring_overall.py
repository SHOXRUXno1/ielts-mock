"""Tests for server-side overall_band recomputation in speaking scoring."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.llm import _recompute_overall_band, evaluate_speaking_dialog


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

        assert result["overall_band"] == 6.5
        assert result["transcript"] == "I live in a small city near the mountains."
