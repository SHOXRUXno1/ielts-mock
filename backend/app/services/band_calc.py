"""Centralized overall band calculation.

Only sections with a positive band score contribute to the overall.
Sections that were not attempted (None) or scored 0.0 (no questions answered)
are excluded from the average.
"""

from app.models.attempt import Attempt


def compute_overall_band(attempt: Attempt) -> float | None:
    bands = [
        b for b in [
            attempt.listening_band,
            attempt.reading_band,
            attempt.writing_band,
            attempt.speaking_band,
        ]
        if b is not None and b > 0
    ]
    if not bands:
        return None
    return round(sum(bands) / len(bands) * 2) / 2
