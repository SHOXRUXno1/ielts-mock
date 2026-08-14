"""Centralized overall band calculation.

Sections that were not attempted have band = None and are excluded
from the average.  Sections attempted but scored 0.0 (all wrong) ARE
included — they represent a real score, not a skip.

IELTS official rounding: averages are rounded to the nearest 0.5 half-up
(.25 → .5, .75 → next whole).
"""

from __future__ import annotations

import math

from app.models.attempt import Attempt, AttemptStatus


def round_ielts_band(value: float) -> float:
    """Round to nearest 0.5 using half-up (IELTS official).

    Examples: 6.25 → 6.5, 6.75 → 7.0, 6.1 → 6.0, 6.9 → 7.0.
    """
    return math.floor(value * 2 + 0.5) / 2


def compute_overall_band(attempt: Attempt) -> float | None:
    bands = [
        b for b in [
            attempt.listening_band,
            attempt.reading_band,
            attempt.writing_band,
            attempt.speaking_band,
        ]
        if b is not None
    ]
    if len(bands) < 3:
        return None
    return round_ielts_band(sum(bands) / len(bands))


def derive_scored_status(attempt: Attempt) -> AttemptStatus:
    """Determine the terminal status after scoring completes.

    PARTIAL        — 2+ of L/R/W not attempted (band is None).
    FULLY_SCORED   — all 4 sections have a band (including speaking).
    AUTO_SCORED    — L/R/W resolved, speaking not yet done.
    """
    lrw_bands = [attempt.listening_band, attempt.reading_band, attempt.writing_band]
    none_count = sum(1 for b in lrw_bands if b is None)
    if none_count >= 2:
        return AttemptStatus.PARTIAL
    if attempt.speaking_band is not None:
        return AttemptStatus.FULLY_SCORED
    return AttemptStatus.AUTO_SCORED
