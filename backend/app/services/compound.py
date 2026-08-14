"""Compound completion question types (table / note / form / summary).

Structure lives on QuestionGroup.options_shared. Each gap is a separate
Question linked via content.gap_id.

Canonical cell/item/field shape uses ``segments``:
  { "variant": "plain", "segments": [ {"type":"text","value":"..."}, {"type":"gap","gap_id":"g1"} ] }

Table cells may also be bulleted:
  { "variant": "bullets", "bullets": [ {"segments": [...]}, ... ] }

Legacy shapes (pre-segments / missing cell.variant) are still accepted.
"""

from __future__ import annotations

from typing import Any

COMPOUND_TYPES: frozenset[str] = frozenset(
    {
        "table_completion",
        "note_completion",
        "form_completion",
        "summary_completion",
        "flow_chart_completion",
        "diagram_labeling",
    }
)

_VARIANT_FOR_TYPE: dict[str, str] = {
    "table_completion": "table",
    "note_completion": "notes",
    "form_completion": "form",
    "summary_completion": "summary",
    "flow_chart_completion": "flow",
    "diagram_labeling": "notes",
}


def is_compound_type(question_type: str | Any) -> bool:
    value = question_type.value if hasattr(question_type, "value") else str(question_type)
    return value in COMPOUND_TYPES


def _gaps_from_segments(segments: Any) -> list[str]:
    gaps: list[str] = []
    if not isinstance(segments, list):
        return gaps
    for segment in segments:
        if isinstance(segment, dict) and segment.get("type") == "gap":
            gap_id = segment.get("gap_id")
            if isinstance(gap_id, str) and gap_id:
                gaps.append(gap_id)
    return gaps


def _validate_segments(segments: Any, path: str) -> None:
    if not isinstance(segments, list):
        raise ValueError(f"{path} requires segments list")
    if len(segments) == 0:
        raise ValueError(f"{path} requires non-empty segments")
    for si, segment in enumerate(segments):
        if not isinstance(segment, dict) or segment.get("type") not in ("text", "gap"):
            raise ValueError(f"{path} segment [{si}] must be type text|gap")
        if segment["type"] == "text" and "value" not in segment:
            raise ValueError(f"{path} text segment [{si}] requires value")
        if segment["type"] == "gap" and not segment.get("gap_id"):
            raise ValueError(f"{path} gap segment [{si}] requires gap_id")


def extract_gap_ids(structure: dict[str, Any] | None) -> list[str]:
    """Walk any compound variant and return gap_ids in document order.

    Supports both the segments model and legacy cell/item/field shapes.
    """
    if not isinstance(structure, dict):
        return []

    variant = structure.get("variant")
    gaps: list[str] = []

    if variant == "table":
        for row in structure.get("rows") or []:
            if not isinstance(row, list):
                continue
            for cell in row:
                if not isinstance(cell, dict):
                    continue
                cell_variant = cell.get("variant")
                if cell_variant == "bullets" or (
                    "bullets" in cell and cell_variant != "plain"
                ):
                    for bullet in cell.get("bullets") or []:
                        if isinstance(bullet, dict):
                            gaps.extend(_gaps_from_segments(bullet.get("segments")))
                elif "segments" in cell:
                    gaps.extend(_gaps_from_segments(cell.get("segments")))
                elif cell.get("type") == "gap":
                    gap_id = cell.get("gap_id")
                    if isinstance(gap_id, str) and gap_id:
                        gaps.append(gap_id)

    elif variant == "notes":
        for section in structure.get("sections") or []:
            if not isinstance(section, dict):
                continue
            for item in section.get("items") or []:
                if not isinstance(item, dict):
                    continue
                if "segments" in item:
                    gaps.extend(_gaps_from_segments(item.get("segments")))
                elif item.get("type") == "gap_line":
                    gap_id = item.get("gap_id")
                    if isinstance(gap_id, str) and gap_id:
                        gaps.append(gap_id)

    elif variant == "form":
        for field in structure.get("fields") or []:
            if not isinstance(field, dict):
                continue
            if field.get("type") == "gap_line" or "segments" in field:
                gaps.extend(_gaps_from_segments(field.get("segments")))
            elif field.get("type") == "gap":
                gap_id = field.get("gap_id")
                if isinstance(gap_id, str) and gap_id:
                    gaps.append(gap_id)

    elif variant == "summary":
        for paragraph in structure.get("paragraphs") or []:
            if not isinstance(paragraph, dict):
                continue
            gaps.extend(_gaps_from_segments(paragraph.get("segments")))

    elif variant == "flow":
        for step in structure.get("steps") or []:
            if not isinstance(step, dict):
                continue
            gaps.extend(_gaps_from_segments(step.get("segments")))

    return gaps


def validate_compound_structure(
    question_type: str | Any,
    options_shared: dict[str, Any] | None,
) -> None:
    """Validate options_shared for a compound group. Raises ValueError on failure."""
    qtype = question_type.value if hasattr(question_type, "value") else str(question_type)
    if qtype not in COMPOUND_TYPES:
        return

    if not isinstance(options_shared, dict):
        raise ValueError(f"{qtype} requires options_shared structure JSON")

    expected_variant = _VARIANT_FOR_TYPE[qtype]
    variant = options_shared.get("variant")
    if variant != expected_variant:
        raise ValueError(
            f"{qtype} requires options_shared.variant == '{expected_variant}', "
            f"got {variant!r}"
        )

    if "instruction_words" not in options_shared:
        raise ValueError(f"{qtype} requires options_shared.instruction_words")

    max_words = options_shared.get("max_words_per_gap", 2)
    if not isinstance(max_words, int) or max_words < 1:
        raise ValueError(f"{qtype} requires max_words_per_gap to be a positive integer")

    if variant == "table":
        headers = options_shared.get("headers")
        rows = options_shared.get("rows")
        if not isinstance(headers, list) or len(headers) == 0:
            raise ValueError("table_completion requires non-empty headers")
        if not isinstance(rows, list) or len(rows) == 0:
            raise ValueError("table_completion requires non-empty rows")
        for ri, row in enumerate(rows):
            if not isinstance(row, list):
                raise ValueError(f"table row {ri} must be a list of cells")
            if len(row) != len(headers):
                raise ValueError(
                    f"table row {ri} has {len(row)} cells, expected {len(headers)}"
                )
            for ci, cell in enumerate(row):
                if not isinstance(cell, dict):
                    raise ValueError(f"table cell [{ri}][{ci}] must be an object")
                cell_variant = cell.get("variant")
                path = f"table cell [{ri}][{ci}]"
                if cell_variant == "bullets" or (
                    "bullets" in cell and cell_variant != "plain"
                ):
                    bullets = cell.get("bullets")
                    if not isinstance(bullets, list) or len(bullets) == 0:
                        raise ValueError(f"{path} bullets requires non-empty bullets list")
                    for bi, bullet in enumerate(bullets):
                        if not isinstance(bullet, dict):
                            raise ValueError(f"{path} bullet [{bi}] must be an object")
                        _validate_segments(bullet.get("segments"), f"{path} bullet [{bi}]")
                elif cell_variant == "plain" or "segments" in cell:
                    _validate_segments(cell.get("segments"), path)
                elif cell.get("type") in ("text", "gap"):
                    # Legacy shape
                    if cell["type"] == "text" and "value" not in cell:
                        raise ValueError(f"table text cell [{ri}][{ci}] requires value")
                    if cell["type"] == "gap" and not cell.get("gap_id"):
                        raise ValueError(f"table gap cell [{ri}][{ci}] requires gap_id")
                else:
                    raise ValueError(
                        f"{path} must be variant plain|bullets "
                        "(or legacy segments / type text|gap)"
                    )

    elif variant == "notes":
        sections = options_shared.get("sections")
        if not isinstance(sections, list) or len(sections) == 0:
            raise ValueError("note_completion requires non-empty sections")
        for si, section in enumerate(sections):
            if not isinstance(section, dict):
                raise ValueError(f"notes section {si} must be an object")
            items = section.get("items")
            if not isinstance(items, list):
                raise ValueError(f"notes section {si} requires items list")
            for ii, item in enumerate(items):
                if not isinstance(item, dict):
                    raise ValueError(f"notes item [{si}][{ii}] must be an object")
                if "segments" in item:
                    _validate_segments(item.get("segments"), f"notes item [{si}][{ii}]")
                elif item.get("type") in ("text", "gap_line"):
                    # Legacy shape
                    if item["type"] == "text" and "value" not in item:
                        raise ValueError(f"notes text item [{si}][{ii}] requires value")
                    if item["type"] == "gap_line" and not item.get("gap_id"):
                        raise ValueError(f"notes gap_line [{si}][{ii}] requires gap_id")
                else:
                    raise ValueError(
                        f"notes item [{si}][{ii}] must have segments or type text|gap_line"
                    )

    elif variant == "form":
        if not options_shared.get("form_title"):
            raise ValueError("form_completion requires form_title")
        fields = options_shared.get("fields")
        if not isinstance(fields, list) or len(fields) == 0:
            raise ValueError("form_completion requires non-empty fields")
        for fi, field in enumerate(fields):
            if not isinstance(field, dict):
                raise ValueError(f"form field {fi} must be an object")
            if "label" not in field:
                raise ValueError(f"form field {fi} requires label")
            ftype = field.get("type")
            if ftype == "static":
                if "value" not in field:
                    raise ValueError(f"form static field {fi} requires value")
            elif ftype == "gap_line" or ("segments" in field and ftype != "gap"):
                _validate_segments(field.get("segments"), f"form field {fi}")
            elif ftype == "gap":
                # Legacy shape
                if not field.get("gap_id"):
                    raise ValueError(f"form gap field {fi} requires gap_id")
            else:
                raise ValueError(
                    f"form field {fi} must be type static|gap_line (or legacy gap)"
                )

    elif variant == "summary":
        paragraphs = options_shared.get("paragraphs")
        if not isinstance(paragraphs, list) or len(paragraphs) == 0:
            raise ValueError("summary_completion requires non-empty paragraphs")
        for pi, paragraph in enumerate(paragraphs):
            if not isinstance(paragraph, dict):
                raise ValueError(f"summary paragraph {pi} must be an object")
            _validate_segments(paragraph.get("segments"), f"summary paragraph {pi}")

    elif variant == "flow":
        steps = options_shared.get("steps")
        if not isinstance(steps, list) or len(steps) == 0:
            raise ValueError("flow_chart_completion requires non-empty steps")
        for si, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError(f"flow step {si} must be an object")
            _validate_segments(step.get("segments"), f"flow step {si}")

    gap_ids = extract_gap_ids(options_shared)
    if not gap_ids:
        raise ValueError(f"{qtype} structure must contain at least one gap")
    if len(gap_ids) != len(set(gap_ids)):
        raise ValueError(f"{qtype} structure has duplicate gap_id values")


def validate_compound_gap_content(
    group_question_type: str | Any,
    options_shared: dict[str, Any] | None,
    content: dict[str, Any] | None,
) -> None:
    """Ensure question.content.gap_id exists in the group's structure."""
    if not is_compound_type(group_question_type):
        return
    if not isinstance(content, dict):
        raise ValueError("Compound gap question requires content with gap_id")
    gap_id = content.get("gap_id")
    if not isinstance(gap_id, str) or not gap_id:
        raise ValueError("Compound gap question requires content.gap_id")
    known = set(extract_gap_ids(options_shared))
    if gap_id not in known:
        raise ValueError(
            f"gap_id '{gap_id}' is not present in group structure. "
            f"Known gaps: {sorted(known)}"
        )


def check_compound_group_completeness(
    question_type: str | Any,
    options_shared: dict[str, Any] | None,
    questions: list[Any],
) -> list[str]:
    """Return publish errors if structure gaps and questions don't match 1:1."""
    if not is_compound_type(question_type):
        return []

    qtype = question_type.value if hasattr(question_type, "value") else str(question_type)
    errors: list[str] = []
    try:
        validate_compound_structure(qtype, options_shared)
    except ValueError as exc:
        errors.append(f"{qtype} group: {exc}")
        return errors

    structure_gaps = extract_gap_ids(options_shared)
    structure_set = set(structure_gaps)
    question_gaps: list[str] = []
    for q in questions:
        content = q.content if isinstance(getattr(q, "content", None), dict) else {}
        gap_id = content.get("gap_id")
        if isinstance(gap_id, str) and gap_id:
            question_gaps.append(gap_id)

    question_set = set(question_gaps)
    missing = structure_set - question_set
    extra = question_set - structure_set
    if missing:
        errors.append(
            f"{qtype} group is missing questions for gap_id(s): {sorted(missing)}"
        )
    if extra:
        errors.append(
            f"{qtype} group has questions with unknown gap_id(s): {sorted(extra)}"
        )
    if len(question_gaps) != len(question_set):
        errors.append(f"{qtype} group has duplicate gap_id questions")
    return errors
