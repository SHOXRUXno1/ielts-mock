"""Duration rules per section type (pure, no DB I/O).

Source of truth for how long a section may run in computer-delivered IELTS.
"""

from __future__ import annotations

from typing import TypedDict

from app.models.section import SectionType


class DurationRule(TypedDict):
    min: int | None
    max: int | None
    recommended: int | None
    # Soft band around recommended: within this, no warning toast.
    tolerance: int


DURATION_RULES: dict[str, DurationRule] = {
    SectionType.LISTENING.value: {
        "min": 20,
        "max": 45,
        "recommended": 30,
        "tolerance": 3,
    },
    SectionType.READING.value: {
        "min": 45,
        "max": 75,
        "recommended": 60,
        "tolerance": 5,
    },
    SectionType.WRITING.value: {
        "min": 45,
        "max": 75,
        "recommended": 60,
        "tolerance": 5,
    },
    # Speaking is AI-paced: NULL means untimed, a number acts as a hard cap.
    SectionType.SPEAKING.value: {
        "min": 1,
        "max": 20,
        "recommended": None,
        "tolerance": 0,
    },
}

# Used only to estimate total test duration in the UI.
SPEAKING_TYPICAL_MINUTES = 12

DURATION_MODES = ("standard", "custom")


class DurationRangeError(ValueError):
    """Raised when a duration falls outside the allowed range for its type."""


def _type_value(section_type) -> str:
    if isinstance(section_type, SectionType):
        return section_type.value
    return str(section_type)


def rule_for(section_type) -> DurationRule:
    stype = _type_value(section_type)
    rule = DURATION_RULES.get(stype)
    if rule is None:
        raise DurationRangeError(f"Unknown section type '{stype}'")
    return rule


def recommended_for(section_type) -> int | None:
    """Recommended duration, or None for untimed types (speaking)."""
    return rule_for(section_type)["recommended"]


def default_settings() -> dict[str, int | None]:
    """Recommended duration for every section type, keyed by type value."""
    return {stype: rule["recommended"] for stype, rule in DURATION_RULES.items()}


def check_duration(section_type, minutes: int | None) -> str | None:
    """Validate a duration.

    Raises DurationRangeError when out of range. Returns a warning string when
    the value is allowed but differs from the recommendation beyond tolerance,
    else None.
    """
    stype = _type_value(section_type)
    rule = rule_for(stype)
    label = stype.capitalize()
    recommended = rule["recommended"]
    tolerance = rule["tolerance"]

    if minutes is None:
        # Only speaking may be untimed. Timed sections must always have a value.
        if recommended is None:
            return None
        raise DurationRangeError(
            f"{label} duration cannot be null. Recommended: {recommended}."
        )

    if minutes <= 0:
        raise DurationRangeError(f"{label} duration must be a positive number of minutes.")

    lo, hi = rule["min"], rule["max"]
    if (lo is not None and minutes < lo) or (hi is not None and minutes > hi):
        raise DurationRangeError(_range_message(label, lo, hi, recommended))

    if recommended is None:
        return (
            f"{label} is normally untimed — AI controls pacing. "
            f"{minutes} min will act as a hard cap."
        )
    if abs(minutes - recommended) <= tolerance:
        return None
    return (
        f"You set {minutes} min. Computer-delivered IELTS uses "
        f"{recommended} min for {label}."
    )


def _range_message(
    label: str,
    lo: int | None,
    hi: int | None,
    recommended: int | None,
) -> str:
    if lo is not None and hi is not None:
        span = f"{lo}-{hi}"
    elif hi is not None:
        span = f"at most {hi}"
    else:
        span = f"at least {lo}"
    msg = f"{label} duration must be {span} min."
    if recommended is not None:
        msg += f" Recommended: {recommended}."
    return msg


def total_minutes(durations: dict[str, int | None]) -> int:
    """Estimated total test duration; speaking falls back to a typical value."""
    total = 0
    for stype, minutes in durations.items():
        if minutes is not None:
            total += minutes
        elif stype == SectionType.SPEAKING.value:
            total += SPEAKING_TYPICAL_MINUTES
    return total

