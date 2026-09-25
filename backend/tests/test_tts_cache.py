"""TTS cache keys carry a fingerprint of the current voice/model settings.

The cache used to key on `text` alone. When the operator bumped a voice
setting (say, `stability` or `model_id`), the old MP3 kept being served
until each gunicorn worker was restarted. Fingerprinting the key means any
config change invalidates matching entries naturally — new writes shadow
them and the LRU walks them out.
"""

from unittest.mock import patch

from app.services import tts_cache


def _configure(mock_settings, **overrides) -> None:
    mock_settings.elevenlabs_model_id = "eleven_turbo_v2_5"
    mock_settings.elevenlabs_voice_id = "voice123"
    mock_settings.elevenlabs_stability = 0.5
    mock_settings.elevenlabs_similarity_boost = 0.75
    mock_settings.elevenlabs_style = 0.3
    mock_settings.elevenlabs_use_speaker_boost = True
    mock_settings.elevenlabs_speed = 0.9
    mock_settings.elevenlabs_output_format = "mp3_44100_192"
    for k, v in overrides.items():
        setattr(mock_settings, k, v)


class TestFingerprintedCache:
    def setup_method(self):
        tts_cache.clear_tts_cache()

    def test_cache_hit_with_identical_settings(self):
        with patch("app.services.tts_cache.settings") as mock_settings:
            _configure(mock_settings)
            tts_cache.set_cached_tts("Hello.", "base64-a")
            assert tts_cache.get_cached_tts("Hello.") == "base64-a"

    def test_model_change_invalidates_entry(self):
        with patch("app.services.tts_cache.settings") as mock_settings:
            _configure(mock_settings, elevenlabs_model_id="eleven_flash_v2_5")
            tts_cache.set_cached_tts("Hello.", "flash-audio")

        with patch("app.services.tts_cache.settings") as mock_settings:
            _configure(mock_settings, elevenlabs_model_id="eleven_turbo_v2_5")
            assert tts_cache.get_cached_tts("Hello.") is None

    def test_voice_settings_change_invalidates_entry(self):
        with patch("app.services.tts_cache.settings") as mock_settings:
            _configure(mock_settings, elevenlabs_stability=0.75)
            tts_cache.set_cached_tts("Hello.", "old-stability-audio")

        with patch("app.services.tts_cache.settings") as mock_settings:
            _configure(mock_settings, elevenlabs_stability=0.5)
            assert tts_cache.get_cached_tts("Hello.") is None

    def test_output_format_change_invalidates_entry(self):
        with patch("app.services.tts_cache.settings") as mock_settings:
            _configure(mock_settings, elevenlabs_output_format="mp3_44100_128")
            tts_cache.set_cached_tts("Hello.", "128kbps-audio")

        with patch("app.services.tts_cache.settings") as mock_settings:
            _configure(mock_settings, elevenlabs_output_format="mp3_44100_192")
            assert tts_cache.get_cached_tts("Hello.") is None

    def test_different_texts_dont_collide(self):
        with patch("app.services.tts_cache.settings") as mock_settings:
            _configure(mock_settings)
            tts_cache.set_cached_tts("Alpha.", "audio-a")
            tts_cache.set_cached_tts("Beta.", "audio-b")
            assert tts_cache.get_cached_tts("Alpha.") == "audio-a"
            assert tts_cache.get_cached_tts("Beta.") == "audio-b"
