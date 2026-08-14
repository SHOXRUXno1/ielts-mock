"""Guards against orphan / ghost questions that break take UI and scoring."""

from __future__ import annotations

from typing import Any


def orphan_question_errors(test: Any) -> list[str]:
    """Return publish errors for questions that are not attached to a group.

    Orphans on Listening/Reading previously rendered as ghost rows
    (``Question type "note_completion"``) and skewed display numbering.
    """
    errors: list[str] = []
    for section in getattr(test, "sections", []) or []:
        stype = getattr(section.type, "value", section.type)
        for q in getattr(section, "questions", []) or []:
            if getattr(q, "question_group_id", None) is None:
                errors.append(
                    f"{str(stype).capitalize()} section order={section.order}: "
                    f"question order={q.order} has no question group "
                    f"(orphan {getattr(q, 'question_type', '?')}). "
                    "Delete it or attach it to a group before publishing."
                )
    return errors
