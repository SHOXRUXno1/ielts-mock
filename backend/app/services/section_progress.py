"""Pure section-progress state machine (no DB I/O)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, Sequence

from app.models.section import SectionType
from app.models.section_progress import SectionProgress, SectionState, SealedReason
from app.models.test_section_settings import TestSectionSettings

GRACE_SECONDS = 30

# Speaking is AI-paced; this hard cap only guards against runaway sessions.
SPEAKING_HARD_CAP_MINUTES = 20

SEAL_REASON_MANUAL = SealedReason.MANUAL.value
SEAL_REASON_TIMEOUT = SealedReason.TIMEOUT.value
SEAL_REASON_SUBMIT = SealedReason.SUBMIT.value
SEAL_REASON_ADVANCE = SealedReason.ADVANCE.value

TYPE_ORDER: tuple[str, ...] = (
    SectionType.LISTENING.value,
    SectionType.READING.value,
    SectionType.WRITING.value,
    SectionType.SPEAKING.value,
)


class SectionProgressError(Exception):
    """Base error for section-progress transitions."""

    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class SectionConflictError(SectionProgressError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=409)


def _as_state(value: str | SectionState) -> SectionState:
    if isinstance(value, SectionState):
        return value
    return SectionState(value)


def _section_type_value(section_type: str | SectionType) -> str:
    if isinstance(section_type, SectionType):
        return section_type.value
    return str(section_type)


def type_duration_minutes(
    settings: Sequence[TestSectionSettings],
    section_type: str | SectionType,
) -> int | None:
    """Configured duration for a section type, or None when untimed."""
    stype = _section_type_value(section_type)
    for row in settings:
        if row.section_type == stype:
            return row.duration_minutes
    return None


def compute_ends_at(
    now: datetime,
    settings: Sequence[TestSectionSettings],
    section_type: str | SectionType,
    *,
    override_minutes: int | None = None,
) -> datetime | None:
    """Deadline for a section.

    Timed sections use TestSectionSettings.duration_minutes by default.
    ``override_minutes`` wins when provided (e.g. practice mode uses a
    per-part duration instead of the whole-section budget); pass ``None`` to
    fall back to the section-level setting.
    Speaking with null duration gets a safety hard cap (not a real exam timer).
    """
    stype = _section_type_value(section_type)
    minutes = override_minutes if override_minutes is not None else type_duration_minutes(settings, stype)
    if minutes:
        return now + timedelta(minutes=minutes)
    if stype == SectionType.SPEAKING.value:
        return now + timedelta(minutes=SPEAKING_HARD_CAP_MINUTES)
    return None


def find_row(
    rows: Sequence[SectionProgress],
    section_type: str | SectionType,
) -> SectionProgress | None:
    stype = _section_type_value(section_type)
    for row in rows:
        if row.section_type == stype:
            return row
    return None


def find_active(rows: Sequence[SectionProgress]) -> SectionProgress | None:
    for row in rows:
        if _as_state(row.state) == SectionState.ACTIVE:
            return row
    return None


def is_expired(row: SectionProgress, now: datetime) -> bool:
    """True when now is past ends_at + grace period."""
    if row.ends_at is None:
        return False
    ends = row.ends_at
    if ends.tzinfo is None:
        ends = ends.replace(tzinfo=timezone.utc)
    check = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    return check > ends + timedelta(seconds=GRACE_SECONDS)


def apply_seal(
    row: SectionProgress,
    reason: str,
    now: datetime,
    *,
    sealed_at: datetime | None = None,
) -> SectionProgress:
    """Seal a row in-place. Idempotent if already sealed.

    ``sealed_at`` defaults to ``now``. Timeout seals pass ``ends_at`` so the
    official deadline is recorded rather than the late request time.
    """
    if _as_state(row.state) == SectionState.SEALED:
        return row
    row.state = SectionState.SEALED.value
    row.sealed_at = sealed_at if sealed_at is not None else now
    row.sealed_reason = reason
    return row


def apply_timeout_seal(row: SectionProgress, now: datetime) -> SectionProgress:
    """Seal an expired active section; sealed_at is the official ends_at."""
    official = row.ends_at or now
    return apply_seal(row, SEAL_REASON_TIMEOUT, now, sealed_at=official)


def resolve_present_types(
    rows: Sequence[SectionProgress],
    present_types: Iterable[str] | None = None,
) -> list[str]:
    """Ordered present skill list: explicit present_types, else types in rows."""
    if present_types is not None:
        allowed = {_section_type_value(t) for t in present_types}
    else:
        allowed = {r.section_type for r in rows}
    return [t for t in TYPE_ORDER if t in allowed]


def apply_enter(
    rows: Sequence[SectionProgress],
    settings: Sequence[TestSectionSettings],
    section_type: str | SectionType,
    now: datetime,
    *,
    present_types: Iterable[str] | None = None,
    duration_override_minutes: int | None = None,
) -> tuple[SectionProgress, SectionProgress | None]:
    """Enter a section.

    Returns (entered_row, sealed_previous_or_None).
    Raises SectionConflictError if the target is already sealed, or if prior
    present sections are not sealed yet (sequential exam order).
    Idempotent when the target is already active.

    ``duration_override_minutes`` — bypass ``TestSectionSettings`` for this
    single enter (used by practice mode to enforce a per-part timer).
    """
    stype = _section_type_value(section_type)
    target = find_row(rows, stype)
    if target is None:
        raise SectionProgressError(f"No progress row for section type {stype}")

    state = _as_state(target.state)
    if state == SectionState.SEALED:
        raise SectionConflictError("Section already completed")

    if state == SectionState.ACTIVE:
        return target, None

    # Sequential order: cannot skip a not_started prior skill.
    # ACTIVE prior is OK — it will be advance-sealed below.
    present = resolve_present_types(rows, present_types)
    for prior in present:
        if prior == stype:
            break
        prior_row = find_row(rows, prior)
        if prior_row is None:
            continue
        if _as_state(prior_row.state) == SectionState.NOT_STARTED:
            raise SectionConflictError(
                "Previous sections must be completed first"
            )

    sealed_previous: SectionProgress | None = None
    active = find_active(rows)
    if active is not None and active.section_type != stype:
        apply_seal(active, SEAL_REASON_ADVANCE, now)
        sealed_previous = active

    target.state = SectionState.ACTIVE.value
    target.started_at = now
    target.ends_at = compute_ends_at(
        now, settings, stype, override_minutes=duration_override_minutes
    )
    target.sealed_at = None
    target.sealed_reason = None
    return target, sealed_previous


def next_not_started_type(
    rows: Sequence[SectionProgress],
    present_types: Iterable[str] | None = None,
) -> str | None:
    """First NOT_STARTED section in TYPE_ORDER (suggestion after seal)."""
    by_type = {r.section_type: r for r in rows}
    for t in resolve_present_types(rows, present_types):
        row = by_type.get(t)
        if row is None:
            continue
        if _as_state(row.state) == SectionState.NOT_STARTED:
            return t
    return None


# Back-compat alias used by older call sites.
def next_unsealed_type(
    rows: Sequence[SectionProgress],
    present_types: Iterable[str],
) -> str | None:
    return next_not_started_type(rows, present_types)


def all_sealed(
    rows: Sequence[SectionProgress],
    present_types: Iterable[str] | None = None,
) -> bool:
    """True when every present skill is sealed (orphan progress rows ignored)."""
    present = resolve_present_types(rows, present_types)
    if not present:
        return False
    by_type = {r.section_type: r for r in rows}
    for t in present:
        row = by_type.get(t)
        if row is None or _as_state(row.state) != SectionState.SEALED:
            return False
    return True


def ensure_progress_rows(
    attempt_id,
    present_types: Iterable[str] | None = None,
) -> list[SectionProgress]:
    """Build NOT_STARTED SectionProgress rows for the requested section types.

    Full-mock attempts seed the canonical four types. Practice attempts pass
    ``present_types=[target]`` to seed only the one type they will exercise —
    this keeps the state machine intact without touching the schema.
    """
    types = resolve_present_types([], present_types) if present_types is not None else list(TYPE_ORDER)
    if not types:
        types = list(TYPE_ORDER)
    return [
        SectionProgress(
            attempt_id=attempt_id,
            section_type=t,
            state=SectionState.NOT_STARTED.value,
        )
        for t in types
    ]


def seal_expired_if_needed(
    row: SectionProgress,
    now: datetime,
) -> bool:
    """If active and past grace, seal with timeout. Returns True if sealed now."""
    if _as_state(row.state) != SectionState.ACTIVE:
        return False
    if not is_expired(row, now):
        return False
    apply_timeout_seal(row, now)
    return True


def expired_detail(
    row: SectionProgress,
    next_section: str | None,
) -> dict:
    """Structured 409 body for SECTION_EXPIRED (frontend auto-advance)."""
    ends = row.ends_at
    if ends is not None and ends.tzinfo is None:
        ends = ends.replace(tzinfo=timezone.utc)
    sealed_at = row.sealed_at or ends
    message = "Section time expired"
    if ends is not None:
        message = f"Section time expired at {ends.strftime('%H:%M:%S')}"
    return {
        "code": "SECTION_EXPIRED",
        "message": message,
        "sealed_at": sealed_at.isoformat().replace("+00:00", "Z") if sealed_at else None,
        "next_section": next_section,
    }
