"""Unit tests for the Speaking clarification-request detector."""

import pytest

from app.services.speaking_clarification import (
    MAX_CLARIFICATION_REPEATS,
    is_clarification_request,
)


class TestClarificationExactPhrases:
    """The curated clarification phrases should all match."""

    @pytest.mark.parametrize(
        "phrase",
        [
            "Pardon?",
            "pardon",
            "Pardon me.",
            "Come again?",
            "Say that again",
            "Could you say that again?",
            "Can you say that again please",
            "Please repeat that.",
            "Repeat please",
            "Repeat it.",
            "Could you repeat that?",
            "One more time.",
            "One more time please",
            "What was that?",
            "Could you run that by me again?",
            "Can you run that by me again?",
            "Sorry, what?",
            "Sorry, I missed that.",
            "Sorry I didn't catch that.",
            "I'm sorry I didn't catch that",
            "I am sorry I didn't catch that",
            "Didn't catch that",
            "I didn't catch that",
            "I didn't hear that",
            "I didn't get that",
            "Didn't quite catch that",
            "What did you say?",
            "I beg your pardon",
            "Beg your pardon",
        ],
    )
    def test_matches(self, phrase: str) -> None:
        assert is_clarification_request(phrase), f"should match: {phrase!r}"


class TestClarificationNotMatched:
    """Short Whisper fragments and real answers must NOT match."""

    @pytest.mark.parametrize(
        "phrase",
        [
            # Trimmed ones we explicitly removed from the pattern list —
            # these can be the first word of a real answer when the mic
            # cuts the start.
            "huh",
            "what",
            "what?",
            "what.",
            "pardon?",  # wait — pardon alone IS a match
        ],
    )
    def test_short_ambiguous_not_match_except_pardon(self, phrase: str) -> None:
        # "pardon" is intentionally kept.
        if phrase.lower().strip(" ?.,!") == "pardon":
            assert is_clarification_request(phrase)
        else:
            assert not is_clarification_request(phrase), (
                f"should NOT match (ambiguous Whisper fragment): {phrase!r}"
            )

    @pytest.mark.parametrize(
        "answer",
        [
            # Short valid Part 1 answers
            "Yes, I do.",
            "No, I don't.",
            "Yes",
            "No",
            "Not really.",
            "Probably not.",
            "I agree.",
            "Yeah, I think so.",
            "Of course.",
            "Sometimes.",
            # Long answers
            "Well, I usually eat fast food on weekends with my friends because it's convenient.",
            "The main reason is that it's cheaper and much faster than cooking.",
            # Empty — handled by caller, not by the matcher
            "",
            "   ",
            None,
        ],
    )
    def test_answers_not_matched(self, answer: str | None) -> None:
        assert not is_clarification_request(answer), (
            f"should NOT match (valid answer): {answer!r}"
        )


class TestClarificationCombined:
    """Clarification + answer in the same utterance must go through as an answer.

    This is the critical safety property called out in the design doc:
    anchoring the regex at ^...$ means a long transcript that happens to
    start with 'Sorry' or 'Pardon' is NOT a clarification request.
    """

    @pytest.mark.parametrize(
        "mixed",
        [
            "Sorry, I missed that but I think the main reason is cost.",
            "Pardon me, I was going to say that fast food is unhealthy.",
            "Could you repeat that oh wait I remember now, I usually go on weekends.",
            "Sorry what oh I think the answer is yes.",
            "What did you say I mean yes I do eat fast food sometimes.",
        ],
    )
    def test_mixed_scored_as_answer(self, mixed: str) -> None:
        assert not is_clarification_request(mixed), (
            f"long mixed utterance must score as answer: {mixed!r}"
        )


class TestClarificationNormalization:
    """Punctuation, case and whitespace should not matter."""

    def test_case_insensitive(self) -> None:
        assert is_clarification_request("PARDON")
        assert is_clarification_request("Pardon")

    def test_punctuation_stripped(self) -> None:
        assert is_clarification_request("Pardon?!")
        assert is_clarification_request("...pardon me...")
        assert is_clarification_request("One more time, please.")

    def test_whitespace_collapsed(self) -> None:
        assert is_clarification_request("  pardon  me  ")
        assert is_clarification_request("Could   you   repeat   that")


class TestMaxRepeats:
    """Hard cap exists and is a positive integer."""

    def test_cap_sane(self) -> None:
        assert isinstance(MAX_CLARIFICATION_REPEATS, int)
        assert MAX_CLARIFICATION_REPEATS >= 3
        assert MAX_CLARIFICATION_REPEATS <= 10
