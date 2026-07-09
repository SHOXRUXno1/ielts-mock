"""Shared helper: group items into contiguous runs of the same question type."""
from __future__ import annotations

from typing import Any, Callable


def group_questions_by_contiguous_type(
    items: list[Any],
    type_getter: Callable[[Any], str],
) -> list[list[Any]]:
    """
    Return a list of groups, where each group is a contiguous run of items
    sharing the same question type (as returned by *type_getter*).

    Works generically over dict rows (``type_getter=lambda r: r["question_type"]``)
    and ORM ``Question`` objects (``type_getter=lambda q: q.question_type``).
    """
    if not items:
        return []

    groups: list[list[Any]] = []
    current_type: str | None = None
    current_group: list[Any] = []

    for item in items:
        t = type_getter(item)
        if t != current_type:
            if current_group:
                groups.append(current_group)
            current_type = t
            current_group = [item]
        else:
            current_group.append(item)

    if current_group:
        groups.append(current_group)

    return groups
