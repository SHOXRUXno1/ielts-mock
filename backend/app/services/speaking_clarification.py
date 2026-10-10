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
    # --- Classic polite ---
    r"^pardon$",
    r"^pardon me$",
    r"^come again$",
    r"^(i )?beg your pardon$",
    r"^what was that$",
    r"^what did you say$",
    r"^(could you |can you )?run that by me again$",
    # Standalone "Sorry?" / "Excuse me?" — on their own these are
    # unambiguous clarification tokens. The ^...$ anchors mean any
    # longer utterance ("sorry let me think about that") falls through.
    r"^sorry$",
    r"^excuse me$",
    # --- "Sorry, ..." compounds ---
    r"^sorry what$",
    r"^sorry i missed that$",
    r"^(i am |i'?m )?sorry i did ?n'?t (catch|hear|get) that$",
    r"^(i am |i'?m )?sorry (i am |i'?m )?not with you$",
    # --- Didn't catch / understand ---
    r"^(i )?did ?n'?t (catch|hear|get) that$",
    r"^(i )?did ?n'?t quite (catch|hear|get) that$",
    # "(I) don't / didn't understand (the question)" — very common for
    # B1-B2 CIS students. Requires a verb-phrase after; a bare "I don't"
    # or "understand" alone will not match.
    r"^(i )?(do ?n'?t|did ?n'?t) understand( the question)?$",
    # --- "Say / repeat (it|that|the question) ..." ---
    # Target texts: that, it, the question. The old patterns only had
    # (that|it); non-native students often say "the question" explicitly.
    r"^(could you |can you )?(please )?say (that|it|the question) again( please)?$",
    r"^(could you |can you )?(please )?repeat (that|it|the question)( please)?$",
    r"^(could you |can you )?(please )?repeat( please)?$",
    r"^(could you |can you )?say (that|it|the question) one more time( please)?$",
    r"^(could you |can you )?say (it|that) (one more time|again)( please)?$",
    r"^say again( please)?$",
    r"^one more time( please)?$",
    # "Again please" — bare "again" is too ambiguous (might be a mic
    # fragment), so require "please" as a safety qualifier.
    r"^again please$",
    # --- "Ask again" variants ---
    r"^(could you |can you )?(please )?ask (that |it |the question )?again( please)?$",
    r"^please ask again$",
    r"^(could you |can you )?(please )?explain (that|it|the question)( please)?$",
    # --- "Would you mind ..." (very polite British) ---
    r"^would you mind (repeating|saying) (that|it)( again)?$",
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
