"""Unit tests for speaking examiner context built from test content."""

from types import SimpleNamespace

from app.services.speaking_context import format_speaking_context_from_sections


def _section(order: int, content: dict) -> SimpleNamespace:
    q = SimpleNamespace(
        order=1,
        question_type="speaking_part",
        content=content,
    )
    return SimpleNamespace(order=order, type="speaking", questions=[q])


class TestFormatSpeakingContext:
    def test_full_parts(self):
        sections = [
            _section(30, {"part": 1, "questions": ["Do you like music?", "Where are you from?"]}),
            _section(
                31,
                {
                    "part": 2,
                    "cue_card": {
                        "topic": "a memorable journey",
                        "bullets": ["Where you went", "Who you went with"],
                        "follow_up": "why it was memorable",
                    },
                },
            ),
            _section(32, {"part": 3, "questions": ["Why do people travel?"]}),
        ]
        text = format_speaking_context_from_sections(sections)
        assert text is not None
        assert "PART 1 QUESTIONS" in text
        assert "Do you like music?" in text
        assert "PART 2 CUE CARD" in text
        assert "a memorable journey" in text
        assert "PART 3 QUESTIONS" in text
        assert "Why do people travel?" in text

    def test_empty_returns_none(self):
        sections = [
            _section(30, {"part": 1, "questions": []}),
            _section(31, {"part": 2, "cue_card": {"topic": "", "bullets": []}}),
        ]
        assert format_speaking_context_from_sections(sections) is None

    def test_legacy_prompt_shape(self):
        sections = [_section(30, {"part": 1, "prompt": "Tell me about your hometown."})]
        text = format_speaking_context_from_sections(sections)
        assert text is not None
        assert "Tell me about your hometown." in text
