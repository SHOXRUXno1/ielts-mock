"""An unrecognised name must not end the exam before the first question.

Whisper invents a phrase when handed silence, and that invention used to become
the candidate's answer. Discarding it is right, but discarding it at the intro
means the candidate answers "what should I call you?" into a microphone that
recorded nothing and is told to try again, forever: five live sittings sat on
the greeting until the students gave up and restarted.

Nothing said during the intro is marked, and the engine already has a frame for
an unknown name, so silence there carries the test forward.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.api.speaking_examiner import _is_intro_state
from app.models.speaking_session import SpeakingState
from app.services.llm import Transcription

AUDIO = ("recording.webm", b"x" * 2048, "audio/webm")

HEARD_NOTHING = Transcription(
    text="", provider="groq", latency_ms=610, audio_bytes=2048
)

# What the engine hands back once the intro has been carried forward without a
# name: the Part 1 frame that INTRO_FRAME_NO_NAME already exists to produce.
ADVANCED_TURN = {
    "text": "Alright. Now, in this first part, I'd like to ask you some questions.",
    "audio_base64": "",
    "part": 1,
    "is_end": False,
    "question_number": 1,
    "questions_total": 5,
}


def _session(state: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        current_state=state,
        history_json=[],
        test_id=uuid.uuid4(),
        attempt_id=uuid.uuid4(),
    )


class TestIsIntroState:
    @pytest.mark.parametrize(
        "state",
        [SpeakingState.INTRO_GREETING.value, SpeakingState.INTRO_NICKNAME.value],
    )
    def test_the_name_exchange(self, state):
        assert _is_intro_state(_session(state)) is True

    @pytest.mark.parametrize(
        "state",
        [
            SpeakingState.PART_1_ACTIVE.value,
            SpeakingState.PART_3_ACTIVE.value,
        ],
    )
    def test_the_marked_parts(self, state):
        assert _is_intro_state(_session(state)) is False

    def test_no_session_at_all(self):
        assert _is_intro_state(None) is False


class TestSilenceAtTheIntro:
    def _post(self, client, session):
        with (
            patch(
                "app.api.speaking_examiner.transcribe_audio_bytes_detailed",
                new=AsyncMock(return_value=HEARD_NOTHING),
            ),
            patch(
                "app.api.speaking_examiner._get_live_session",
                new=AsyncMock(return_value=session),
            ),
            patch(
                "app.api.speaking_examiner.load_speaking_plan",
                new=AsyncMock(return_value=object()),
            ),
            patch(
                "app.api.speaking_examiner._advance_turn",
                new=AsyncMock(return_value=dict(ADVANCED_TURN)),
            ),
        ):
            return client.post(
                "/admin/speaking-examiner/transcribe-and-respond",
                params={"session_id": str(session.id)},
                files={"file": AUDIO},
            )

    def test_unrecognised_name_moves_the_test_on(self, auth_client):
        resp = self._post(auth_client, _session(SpeakingState.INTRO_GREETING.value))
        assert resp.status_code == 200, resp.text

    def test_unrecognised_nickname_moves_the_test_on(self, auth_client):
        resp = self._post(auth_client, _session(SpeakingState.INTRO_NICKNAME.value))
        assert resp.status_code == 200, resp.text

    def test_silence_in_a_marked_part_still_asks_again(self, auth_client):
        """Outside the intro the answer counts, so guessing at it would be worse."""
        resp = self._post(auth_client, _session(SpeakingState.PART_1_ACTIVE.value))
        assert resp.status_code == 400
        assert "detect speech" in resp.json()["detail"].lower()
