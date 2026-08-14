"""IELTS display question numbers (computed, not stored).

``question.order`` is group-local (1..N). Display numbers are derived from:
  section_offset (1-based) + cumulative scoring slots across groups.

Section offset = sum of scoring slots in prior sections of the same type + 1.
This is dynamic (not hardcoded 14/27) so non-standard passage sizes work.
"""

from __future__ import annotations

from typing import Any

from app.services.scoring import (
    assign_groups_slot_numbers,
    scoring_slots_for_question,
)


def compute_section_offset(
    section: object,
    prior_sections_same_type: list[object],
) -> int:
    """1-based IELTS number of the first question in *section*.

    ``prior_sections_same_type`` must already be filtered to the same
    ``section.type`` and ordered by ``section.order`` ascending, containing
    only sections that come *before* this one.
    """
    prior_slots = 0
    for prior in prior_sections_same_type:
        prior_slots += _section_scoring_slots(prior)
    return prior_slots + 1


def _section_scoring_slots(section: object) -> int:
    """Sum scoring slots for a section (prefer groups, fall back to flat qs)."""
    groups = getattr(section, "question_groups", None) or []
    if groups:
        total = 0
        for g in groups:
            for q in getattr(g, "questions", None) or []:
                total += scoring_slots_for_question(q)
        return total
    questions = getattr(section, "questions", None) or []
    return sum(scoring_slots_for_question(q) for q in questions)


def _groups_for_section(section: object) -> list[object]:
    groups = list(getattr(section, "question_groups", None) or [])
    if groups:
        return groups
    # Flat questions with no groups — wrap as a synthetic single group so
    # assign_groups_slot_numbers still works.
    questions = list(getattr(section, "questions", None) or [])
    if not questions:
        return []
    from types import SimpleNamespace

    return [
        SimpleNamespace(
            id="__flat__",
            order=1,
            question_type=None,
            questions=questions,
        )
    ]


def question_numbers_for_section(
    section: object,
    prior_sections_same_type: list[object] | None = None,
) -> dict[str, tuple[int, int]]:
    """``{question_id: (start, end)}`` for one section."""
    offset = compute_section_offset(section, prior_sections_same_type or [])
    # assign_groups_slot_numbers uses base_offset where first Q = base_offset+1
    return assign_groups_slot_numbers(
        _groups_for_section(section),
        base_offset=offset - 1,
    )


def question_numbers_for_test(test: object) -> dict[str, tuple[int, int]]:
    """``{question_id: (start, end)}`` across all sections of a test."""
    sections = sorted(
        getattr(test, "sections", None) or [],
        key=lambda s: getattr(s, "order", 0),
    )
    # Group by type, accumulate offset within each type.
    by_type: dict[Any, list[object]] = {}
    for s in sections:
        stype = getattr(s, "type", None)
        key = getattr(stype, "value", stype)
        by_type.setdefault(key, []).append(s)

    result: dict[str, tuple[int, int]] = {}
    for _stype, typed in by_type.items():
        typed_sorted = sorted(typed, key=lambda s: getattr(s, "order", 0))
        for i, section in enumerate(typed_sorted):
            prior = typed_sorted[:i]
            result.update(question_numbers_for_section(section, prior))
    return result


def compute_question_number(question: object, test: object | None = None) -> int:
    """Single-question wrapper — returns the inclusive start display number.

    Prefer ``question_numbers_for_test`` / ``annotate_question_numbers`` for
    bulk use. When *test* is provided, numbers are computed across the whole
    test; otherwise only the question's own section is used (offset = 1).
    """
    qid = str(getattr(question, "id", ""))
    if test is not None:
        ranges = question_numbers_for_test(test)
    else:
        section = getattr(question, "section", None)
        if section is None:
            group = getattr(question, "group", None)
            section = getattr(group, "section", None) if group else None
        if section is None:
            return getattr(question, "order", 1) or 1
        ranges = question_numbers_for_section(section, [])
    pair = ranges.get(qid)
    return pair[0] if pair else (getattr(question, "order", 1) or 1)


def annotate_question_numbers(
    obj: object,
    *,
    prior_sections_same_type: list[object] | None = None,
) -> None:
    """Set transient ``computed_number`` / ``computed_number_end`` on questions.

    Accepts a Test (annotates all sections) or a Section (optionally with
    prior siblings for correct offset). Attributes are NOT mapped columns —
    Pydantic ``QuestionRead`` picks them up via ``from_attributes``.
    """
    # Detect Test vs Section by presence of .sections
    if hasattr(obj, "sections") and getattr(obj, "sections", None) is not None:
        ranges = question_numbers_for_test(obj)
        for section in getattr(obj, "sections", []) or []:
            _annotate_section_questions(section, ranges)
        return

    # Section
    ranges = question_numbers_for_section(obj, prior_sections_same_type)
    _annotate_section_questions(obj, ranges)


def _annotate_section_questions(
    section: object,
    ranges: dict[str, tuple[int, int]],
) -> None:
    seen: set[str] = set()
    for group in getattr(section, "question_groups", None) or []:
        for q in getattr(group, "questions", None) or []:
            _set_numbers(q, ranges)
            seen.add(str(getattr(q, "id", "")))
    for q in getattr(section, "questions", None) or []:
        qid = str(getattr(q, "id", ""))
        if qid in seen:
            # Same ORM instance may appear via both paths; still set attrs.
            _set_numbers(q, ranges)
            continue
        _set_numbers(q, ranges)


def _set_numbers(q: object, ranges: dict[str, tuple[int, int]]) -> None:
    qid = str(getattr(q, "id", ""))
    pair = ranges.get(qid)
    if pair is None:
        # Fallback: leave unset so schema default (None) is used
        setattr(q, "computed_number", None)
        setattr(q, "computed_number_end", None)
        return
    start, end = pair
    setattr(q, "computed_number", start)
    setattr(q, "computed_number_end", end if end != start else None)


def annotate_questions_list(
    questions: list[object],
    ranges: dict[str, tuple[int, int]],
) -> None:
    """Annotate a flat list of questions given a precomputed ranges map."""
    for q in questions:
        _set_numbers(q, ranges)
