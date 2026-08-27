"""Centralized overall band calculation.

A full-mock overall is always the official 4-skill IELTS average.
Skipped or missing skills count as 0.0 — otherwise a student who
walks out of Speaking would keep the same overall as someone who sat it.

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
        attempt.listening_band,
        attempt.reading_band,
        attempt.writing_band,
        attempt.speaking_band,
    ]
    if all(b is None for b in bands):
        return None
    total = sum(0.0 if b is None else float(b) for b in bands)
    return round_ielts_band(total / 4)


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
