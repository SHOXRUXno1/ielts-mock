"""Clarification-request detection for the AI Speaking Examiner.

A clarification request ("Pardon?", "Could you repeat that?") must NOT be
scored as an answer and must NOT advance ``current_question_index``. The
examiner should instead re-emit the current question. Detection is purely
deterministic (no Gemini) and runs before any state transition.
"""

from __future__ import annotations

import re
import string

# Hard cap on consecutive clarification requests for a single question.
# After this many repeats the examiner force-advances with a warning log,
# so a stuck mic cannot deadlock the session on one question for all 15
# MAX_EXAMINER_TURNS. Three polite re-asks (verbatim, "Sure.", "Let me
# rephrase.") plus two buffer attempts.
MAX_CLARIFICATION_REPEATS = 5

# IMPORTANT: every pattern is anchored ^...$ (full-string match on the
# normalized transcript). This is deliberate: if the student starts with
# "Sorry, I missed that" and THEN actually answers
# ("...oh I think the main reason is..."), the full-string match fails
# and the reply is scored as an answer. Removing the anchors would break
# this safety net — any stray "pardon" buried in a long answer would then
# be mistaken for a repeat request.
#
# Also deliberately absent: single-token patterns like ^huh$, ^what$,
# ^(what|pardon|repeat)$. On a noisy mic Whisper often clips the first
# syllable of a real answer down to one word, and we'd rather score the
# fragment than loop on a phantom clarification.
_CLARIFICATION_PATTERNS: tuple[str, ...] = (
    r"^pardon$",
    r"^pardon me$",
    r"^come again$",
    r"^(could you |can you )?(please )?say that again( please)?$",
    r"^(could you |can you )?(please )?repeat (that|it)( please)?$",
    r"^(could you |can you )?(please )?repeat( please)?$",
    r"^one more time( please)?$",
    r"^(could you |can you )?say it (one more time|again)( please)?$",
    r"^what was that$",
    r"^(could you |can you )?run that by me again$",
    r"^sorry what$",
    r"^sorry i missed that$",
    r"^(i am |i'?m )?sorry i did ?n'?t (catch|hear|get) that$",
    r"^(i )?did ?n'?t (catch|hear|get) that$",
    r"^(i )?did ?n'?t quite (catch|hear|get) that$",
    r"^what did you say$",
    r"^(i )?beg your pardon$",
)

_COMPILED = tuple(re.compile(p) for p in _CLARIFICATION_PATTERNS)
_PUNCT_TABLE = str.maketrans("", "", string.punctuation)
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    """lowercase + strip punctuation + collapse whitespace."""
    if not text:
        return ""
    stripped = text.strip().lower().translate(_PUNCT_TABLE)
    return _WHITESPACE_RE.sub(" ", stripped).strip()


def is_clarification_request(text: str | None) -> bool:
    """True if the normalized transcript matches a repeat-request pattern.

    An empty / whitespace-only transcript is NOT a clarification by this
    helper — callers decide separately how to treat silence (currently:
    silence in a non-intro state is also treated as a clarification by
    the caller, so the examiner re-asks instead of 400'ing).
    """
    normalized = _normalize(text or "")
    if not normalized:
        return False
    for pattern in _COMPILED:
        if pattern.match(normalized):
            return True
    return False
