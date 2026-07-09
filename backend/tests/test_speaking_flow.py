"""Unit tests for server-controlled speaking examiner flow."""

from unittest.mock import AsyncMock, patch

import pytest

from app.api.speaking_examiner import (
    FORCED_END_TEXT,
    MAX_EXAMINER_TURNS,
    QUESTIONS_PER_PART,
    _build_extra_instructions,
    _extract_cue_card,
    _forced_end_payload,
    _next_turn_metadata,
    _parse_tags,
    _question_number_for_part3,
    _resolve_server_metadata,
    count_questions_by_part,
)


def _examiner(text: str = "Question") -> dict:
    return {"role": "examiner", "text": text}


def _candidate(text: str = "Answer") -> dict:
    return {"role": "candidate", "text": text}


def _part1_history(examiner_turns: int) -> list[dict]:
    history: list[dict] = []
    for i in range(examiner_turns):
        history.append(_examiner(f"P1 Q{i + 1}"))
        if i < examiner_turns - 1:
            history.append(_candidate(f"P1 A{i + 1}"))
    return history


class TestCountQuestionsByPart:
    def test_empty_history_starts_part1(self):
        counts = count_questions_by_part([])
        assert counts["part1"] == 0
        assert counts["part2"] == 0
        assert counts["part3"] == 0
        assert counts["current_part"] == 1
        assert counts["should_end"] is False

    def test_after_five_part1_examiner_turns_moves_to_part2(self):
        history = _part1_history(5)
        counts = count_questions_by_part(history)
        assert counts["part1"] == 5
        assert counts["current_part"] == 2
        assert counts["part2"] == 0

    def test_after_cue_card_part2_count_is_one(self):
        history = _part1_history(5)
        history.append(_candidate("P1 A5"))
        history.append(_examiner("Describe a place. [PART:2]"))
        counts = count_questions_by_part(history)
        assert counts["part2"] == 1
        assert counts["current_part"] == 2

    def test_after_thank_you_moves_to_part3(self):
        history = _part1_history(5)
        history.extend([
            _candidate("P1 A5"),
            _examiner("Describe a place."),
            _candidate("monologue"),
            _examiner("Thank you. [PART:3] First P3 question?"),
        ])
        counts = count_questions_by_part(history)
        assert counts["part2"] == 2
        assert counts["current_part"] == 3
        assert counts["part3"] == 0

    def test_should_end_after_four_part3_examiner_turns(self):
        history = _part1_history(5)
        history.extend([
            _candidate("P1 A5"),
            _examiner("Cue card"),
            _candidate("monologue"),
            _examiner("Thank you. P3 Q1"),
        ])
        for i in range(2, QUESTIONS_PER_PART[3] + 1):
            history.append(_candidate(f"P3 A{i - 1}"))
            history.append(_examiner(f"P3 Q{i}"))
        counts = count_questions_by_part(history)
        assert counts["part3"] == QUESTIONS_PER_PART[3] - 1
        assert counts["should_end"] is True


class TestBuildExtraInstructions:
    def test_should_end_directive(self):
        counts = {
            "part1": 5,
            "part2": 2,
            "part3": 4,
            "current_part": 3,
            "should_end": True,
        }
        text = _build_extra_instructions(counts)
        assert "END THE TEST NOW" in text
        assert FORCED_END_TEXT in text

    def test_last_part3_question_at_boundary(self):
        counts = {
            "part1": 5,
            "part2": 2,
            "part3": 2,
            "current_part": 3,
            "should_end": False,
        }
        text = _build_extra_instructions(counts)
        assert "LAST question" in text

    def test_thank_you_and_part3_after_monologue(self):
        counts = {
            "part1": 5,
            "part2": 1,
            "part3": 0,
            "current_part": 2,
            "should_end": False,
        }
        text = _build_extra_instructions(counts)
        assert "Thank you" in text
        assert "[PART:3]" in text

    def test_cue_card_when_part2_starts(self):
        counts = {
            "part1": 5,
            "part2": 0,
            "part3": 0,
            "current_part": 2,
            "should_end": False,
        }
        text = _build_extra_instructions(counts)
        assert "cue card" in text.lower()
        assert "[PART:2]" in text

    def test_last_part1_question_at_four_examiner_turns(self):
        counts = {
            "part1": 4,
            "part2": 0,
            "part3": 0,
            "current_part": 1,
            "should_end": False,
        }
        text = _build_extra_instructions(counts)
        assert "LAST Part 1 question" in text

    def test_no_directive_mid_part1(self):
        counts = {
            "part1": 2,
            "part2": 0,
            "part3": 0,
            "current_part": 1,
            "should_end": False,
        }
        assert _build_extra_instructions(counts) == ""


class TestNextTurnMetadata:
    def test_cue_card_turn_is_part2_question_one(self):
        counts = count_questions_by_part(_part1_history(5) + [_candidate("A5")])
        part, is_end, q = _next_turn_metadata(counts)
        assert part == 2
        assert is_end is False
        assert q == 1

    def test_first_part3_after_monologue(self):
        history = _part1_history(5) + [
            _candidate("A5"),
            _examiner("Cue"),
            _candidate("mono"),
        ]
        counts = count_questions_by_part(history)
        part, is_end, q = _next_turn_metadata(counts)
        assert part == 3
        assert is_end is False
        assert q == 1

    def test_part3_question_numbers_after_thank_you(self):
        history = _part1_history(5) + [
            _candidate("A5"),
            _examiner("Cue"),
            _candidate("mono"),
            _examiner("Thank you. P3 Q1"),
        ]
        counts = count_questions_by_part(history)
        assert _question_number_for_part3(counts) == 2

        history.extend([_candidate("A1"), _examiner("P3 Q2")])
        counts = count_questions_by_part(history)
        assert _question_number_for_part3(counts) == 3

        history.extend([_candidate("A2"), _examiner("P3 Q3")])
        counts = count_questions_by_part(history)
        assert _question_number_for_part3(counts) == 4

    def test_closing_turn_is_end_with_question_four(self):
        history = _part1_history(5) + [
            _candidate("A5"),
            _examiner("Cue"),
            _candidate("mono"),
            _examiner("Thank you. P3 Q1"),
            _candidate("A1"),
            _examiner("P3 Q2"),
            _candidate("A2"),
            _examiner("P3 Q3"),
            _candidate("A3"),
            _examiner("P3 Q4"),
            _candidate("A4"),
        ]
        counts = count_questions_by_part(history)
        part, is_end, q = _next_turn_metadata(counts)
        assert counts["should_end"] is True
        assert part == 3
        assert is_end is True
        assert q == QUESTIONS_PER_PART[3]


class TestResolveServerMetadata:
    def test_strips_cue_card_outside_part2_cue_turn(self):
        counts = count_questions_by_part(_part1_history(2))
        part, is_end, q, cue = _resolve_server_metadata(counts, False, "Describe X")
        assert part == 1
        assert cue is None

    def test_keeps_cue_card_on_cue_turn(self):
        counts = count_questions_by_part(_part1_history(5) + [_candidate("A5")])
        part, is_end, q, cue = _resolve_server_metadata(
            counts,
            False,
            "Describe a book you read.",
        )
        assert part == 2
        assert cue == "Describe a book you read."


class TestParseTags:
    def test_strips_part_and_end_tags(self):
        raw = "Thank you. [PART:3] [END_OF_TEST]"
        clean, part, is_end, cue = _parse_tags(raw)
        assert clean == "Thank you."
        assert part == 3
        assert is_end is True
        assert cue is None

    def test_extracts_cue_card_on_part2(self):
        raw = "Describe a book you read. [PART:2]"
        clean, part, is_end, cue = _parse_tags(raw)
        assert clean == "Describe a book you read."
        assert part == 2
        assert is_end is False
        assert cue == "Describe a book you read."


class TestExtractCueCard:
    def test_legacy_cue_card_tags(self):
        text = "Hello [CUE_CARD]Describe a place[/CUE_CARD]"
        assert _extract_cue_card(text) == "Describe a place"

    def test_describe_topic(self):
        assert _extract_cue_card("Describe your hometown.") == "Describe your hometown."

    def test_no_cue_card(self):
        assert _extract_cue_card("What is your name?") is None


class TestForcedEndPayload:
    @pytest.mark.asyncio
    async def test_forced_end_at_max_turns(self):
        history = [_examiner(f"Q{i}") for i in range(MAX_EXAMINER_TURNS)]
        counts = count_questions_by_part(history)

        with patch(
            "app.api.speaking_examiner._tts_base64",
            new=AsyncMock(return_value=("audio", None, False)),
        ):
            payload = await _forced_end_payload(counts)

        assert payload["text"] == FORCED_END_TEXT
        assert payload["is_end"] is True
        assert payload["part"] == 3
        assert payload["cue_card"] is None
        assert payload["audio_base64"] == "audio"
