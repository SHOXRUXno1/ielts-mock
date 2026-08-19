"""Listening-section audio upload validation."""

from __future__ import annotations

import uuid

from app.api import test_import


def test_rejects_non_audio(auth_client):
    response = auth_client.post(
        f"/admin/tests/{uuid.uuid4()}/audio",
        data={"section_id": str(uuid.uuid4())},
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 422
    assert "Unsupported audio format" in response.json()["detail"]


def test_rejects_empty_mp3(auth_client):
    response = auth_client.post(
        f"/admin/tests/{uuid.uuid4()}/audio",
        data={"section_id": str(uuid.uuid4())},
        files={"file": ("part2.mp3", b"", "audio/mpeg")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty audio file."


def test_rejects_oversize(auth_client, monkeypatch):
    monkeypatch.setattr(test_import, "MAX_AUDIO_BYTES", 8)
    response = auth_client.post(
        f"/admin/tests/{uuid.uuid4()}/audio",
        data={"section_id": str(uuid.uuid4())},
        files={"file": ("part2.mp3", b"0123456789", "audio/mpeg")},
    )
    assert response.status_code == 413
    assert "too large" in response.json()["detail"]
