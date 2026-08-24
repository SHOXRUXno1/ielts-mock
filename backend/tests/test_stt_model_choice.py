"""Hearing a candidate and marking an essay must not share one model setting.

They did. `_gemini_url()` read `gemini_model` for everything, so a model chosen
to suit written work also decided how the exam heard speech — a change nobody
would think to test against audio, made by someone editing a setting whose name
says nothing about listening.

The models are not interchangeable for this. Measured on deliberately
ungrammatical speech, `gemini-3.1-flash-lite` misread accented English that
`gemini-3.5-flash` transcribed correctly, and three other Gemini models could
not accept the audio request at all.
"""

from app.core.config import settings
from app.services.llm import _gemini_url


class TestTheTwoModelsAreChosenSeparately:
    def test_transcription_asks_for_the_speech_model(self):
        assert f"/{settings.gemini_stt_model}:generateContent" in _gemini_url(
            settings.gemini_stt_model
        )

    def test_everything_else_still_asks_for_the_evaluation_model(self):
        assert f"/{settings.gemini_model}:generateContent" in _gemini_url()

    def test_changing_the_essay_model_leaves_speech_alone(self, monkeypatch):
        monkeypatch.setattr(settings, "gemini_model", "some-other-model")

        heard_with = _gemini_url(settings.gemini_stt_model)

        assert "some-other-model" not in heard_with
        assert settings.gemini_stt_model in heard_with

    def test_the_shipped_speech_model_is_one_that_accepts_audio(self):
        """A guard against pasting in a model that 400s on an audio request.

        Of the Gemini models available on our keys, only these three answered an
        inline-audio transcription request: the rest returned 400, sustained
        503s, or nothing at all within 45 seconds.
        """
        assert settings.gemini_stt_model in {
            "gemini-3.5-flash",
            "gemini-3.6-flash",
            "gemini-3.1-flash-lite",
        }
