from unittest.mock import patch

import pytest

from app.api.speaking_examiner import _tts_base64


@pytest.mark.asyncio
async def test_tts_base64_swallows_pipeline_crash():
    with (
        patch("app.api.speaking_examiner.get_cached_tts", return_value=None),
        patch(
            "app.api.speaking_examiner.text_to_speech",
            side_effect=RuntimeError("acquire_nowait missing"),
        ),
    ):
        audio, error, cache_hit = await _tts_base64("Hello")

    assert audio == ""
    assert error == "TTS failed"
    assert cache_hit is False
