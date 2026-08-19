from app.services.storage import _audio_ext


def test_prefers_filename_extension():
    assert _audio_ext("application/octet-stream", "part2.mp3") == "mp3"
    assert _audio_ext("audio/wav", "script.wav") == "wav"
    assert _audio_ext("audio/mp4", "clip.m4a") == "m4a"


def test_falls_back_to_content_type():
    assert _audio_ext("audio/mpeg", "") == "mp3"
    assert _audio_ext("audio/wav", "") == "wav"
