"""Migrate compound options_shared to segments model.

Revision ID: m9a0b1c2d3e4
Revises: l8f9a0b1c2d3
Create Date: 2026-07-10

Rewrites QuestionGroup.options_shared for compound types:

Table cells:
  {type: text, value}  -> {segments: [{type: text, value}]}
  {type: gap, gap_id}  -> {segments: [{type: gap, gap_id}]}

Note items:
  {type: text, value} -> {segments: [{type: text, value}]}
  {type: gap_line, prefix, gap_id, suffix}
    -> {segments: [text(prefix?), gap, text(suffix?)]}

Form fields:
  static unchanged
  {type: gap, label, gap_id, prefix, suffix}
    -> {type: gap_line, label, segments: [text(prefix?), gap, text(suffix?)]}

Summary: unchanged (already segments).

DOWN caveat: mixed text+gap table cells (new capability) collapse to a
single gap cell on downgrade; surrounding static text is dropped because
the legacy model cannot represent mixed cells.
"""

from __future__ import annotations

import copy
import json
import logging
from typing import Any, Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "m9a0b1c2d3e4"
down_revision: Union[str, None] = "l8f9a0b1c2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.runtime.migration")


def _text_seg(value: str) -> dict[str, Any]:
    return {"type": "text", "value": value}


def _gap_seg(gap_id: str) -> dict[str, Any]:
    return {"type": "gap", "gap_id": gap_id}


def _prefix_gap_suffix_segments(
    prefix: Any, gap_id: str, suffix: Any
) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    if isinstance(prefix, str) and prefix:
        segments.append(_text_seg(prefix))
    segments.append(_gap_seg(gap_id))
    if isinstance(suffix, str) and suffix:
        segments.append(_text_seg(suffix))
    return segments


def _upgrade_table_cell(cell: Any) -> Any:
    if not isinstance(cell, dict):
        return cell
    if "segments" in cell:
        return cell
    if cell.get("type") == "text":
        value = cell.get("value", "") if isinstance(cell.get("value"), str) else ""
        return {"segments": [_text_seg(value)]}
    if cell.get("type") == "gap":
        gap_id = cell.get("gap_id")
        if isinstance(gap_id, str) and gap_id:
            return {"segments": [_gap_seg(gap_id)]}
    return cell


def _downgrade_table_cell(cell: Any) -> Any:
    if not isinstance(cell, dict):
        return cell
    segments = cell.get("segments")
    if not isinstance(segments, list):
        return cell

    gaps = [s for s in segments if isinstance(s, dict) and s.get("type") == "gap"]
    texts = [s for s in segments if isinstance(s, dict) and s.get("type") == "text"]

    if gaps:
        gap_id = gaps[0].get("gap_id")
        if isinstance(gap_id, str) and gap_id:
            if len(gaps) > 1 or any(
                isinstance(t.get("value"), str) and t.get("value") for t in texts
            ):
                logger.warning(
                    "Downgrade: mixed/multi-gap table cell collapsed to gap %s",
                    gap_id,
                )
            return {"type": "gap", "gap_id": gap_id}

    value = "".join(
        str(t.get("value", "")) for t in texts if isinstance(t.get("value"), str)
    )
    return {"type": "text", "value": value}


def _upgrade_note_item(item: Any) -> Any:
    if not isinstance(item, dict):
        return item
    # Already migrated (segments without legacy type discriminator)
    if "segments" in item and item.get("type") not in ("text", "gap_line"):
        return {"segments": item["segments"]}

    if item.get("type") == "text":
        value = item.get("value", "") if isinstance(item.get("value"), str) else ""
        return {"segments": [_text_seg(value)]}
    if item.get("type") == "gap_line":
        gap_id = item.get("gap_id")
        if not isinstance(gap_id, str) or not gap_id:
            return item
        return {
            "segments": _prefix_gap_suffix_segments(
                item.get("prefix"), gap_id, item.get("suffix")
            )
        }
    return item


def _downgrade_note_item(item: Any) -> Any:
    if not isinstance(item, dict):
        return item
    segments = item.get("segments")
    if not isinstance(segments, list):
        return item

    gaps = [s for s in segments if isinstance(s, dict) and s.get("type") == "gap"]
    if not gaps:
        value = "".join(
            str(s.get("value", ""))
            for s in segments
            if isinstance(s, dict) and s.get("type") == "text"
        )
        return {"type": "text", "value": value}

    gap_id = gaps[0].get("gap_id")
    if not isinstance(gap_id, str) or not gap_id:
        return item

    prefix_parts: list[str] = []
    suffix_parts: list[str] = []
    seen_gap = False
    for s in segments:
        if not isinstance(s, dict):
            continue
        if s.get("type") == "gap":
            if s.get("gap_id") == gap_id and not seen_gap:
                seen_gap = True
            continue
        if s.get("type") == "text" and isinstance(s.get("value"), str):
            if not seen_gap:
                prefix_parts.append(s["value"])
            else:
                suffix_parts.append(s["value"])

    return {
        "type": "gap_line",
        "gap_id": gap_id,
        "prefix": "".join(prefix_parts),
        "suffix": "".join(suffix_parts),
    }


def _upgrade_form_field(field: Any) -> Any:
    if not isinstance(field, dict):
        return field
    if field.get("type") == "static":
        return field
    if field.get("type") == "gap_line" and "segments" in field:
        return field
    if field.get("type") == "gap":
        gap_id = field.get("gap_id")
        if not isinstance(gap_id, str) or not gap_id:
            return field
        return {
            "type": "gap_line",
            "label": field.get("label", ""),
            "segments": _prefix_gap_suffix_segments(
                field.get("prefix"), gap_id, field.get("suffix")
            ),
        }
    return field


def _downgrade_form_field(field: Any) -> Any:
    if not isinstance(field, dict):
        return field
    if field.get("type") == "static":
        return field
    if field.get("type") != "gap_line":
        return field

    segments = field.get("segments") or []
    gaps = [s for s in segments if isinstance(s, dict) and s.get("type") == "gap"]
    gap_id = gaps[0].get("gap_id") if gaps else "g1"
    if not isinstance(gap_id, str) or not gap_id:
        gap_id = "g1"

    prefix_parts: list[str] = []
    suffix_parts: list[str] = []
    seen_gap = False
    for s in segments:
        if not isinstance(s, dict):
            continue
        if s.get("type") == "gap":
            if not seen_gap:
                seen_gap = True
            continue
        if s.get("type") == "text" and isinstance(s.get("value"), str):
            if not seen_gap:
                prefix_parts.append(s["value"])
            else:
                suffix_parts.append(s["value"])

    return {
        "type": "gap",
        "label": field.get("label", ""),
        "gap_id": gap_id,
        "prefix": "".join(prefix_parts),
        "suffix": "".join(suffix_parts),
    }


def _upgrade_structure(structure: dict[str, Any]) -> dict[str, Any] | None:
    variant = structure.get("variant")
    out = copy.deepcopy(structure)

    if variant == "table":
        rows = out.get("rows")
        if isinstance(rows, list):
            out["rows"] = [
                [_upgrade_table_cell(c) for c in row] if isinstance(row, list) else row
                for row in rows
            ]
        return out

    if variant == "notes":
        sections = out.get("sections")
        if isinstance(sections, list):
            new_sections = []
            for section in sections:
                if not isinstance(section, dict):
                    new_sections.append(section)
                    continue
                sec = copy.deepcopy(section)
                items = sec.get("items")
                if isinstance(items, list):
                    sec["items"] = [_upgrade_note_item(it) for it in items]
                new_sections.append(sec)
            out["sections"] = new_sections
        return out

    if variant == "form":
        fields = out.get("fields")
        if isinstance(fields, list):
            out["fields"] = [_upgrade_form_field(f) for f in fields]
        return out

    if variant == "summary":
        return out

    return None


def _downgrade_structure(structure: dict[str, Any]) -> dict[str, Any] | None:
    variant = structure.get("variant")
    out = copy.deepcopy(structure)

    if variant == "table":
        rows = out.get("rows")
        if isinstance(rows, list):
            out["rows"] = [
                [_downgrade_table_cell(c) for c in row] if isinstance(row, list) else row
                for row in rows
            ]
        return out

    if variant == "notes":
        sections = out.get("sections")
        if isinstance(sections, list):
            new_sections = []
            for section in sections:
                if not isinstance(section, dict):
                    new_sections.append(section)
                    continue
                sec = copy.deepcopy(section)
                items = sec.get("items")
                if isinstance(items, list):
                    sec["items"] = [_downgrade_note_item(it) for it in items]
                new_sections.append(sec)
            out["sections"] = new_sections
        return out

    if variant == "form":
        fields = out.get("fields")
        if isinstance(fields, list):
            out["fields"] = [_downgrade_form_field(f) for f in fields]
        return out

    if variant == "summary":
        return out

    return None


def _rewrite_groups(direction: str) -> None:
    conn = op.get_bind()
    rows = conn.execute(
        text(
            """
            SELECT id, question_type, options_shared
            FROM question_groups
            WHERE question_type IN (
                'table_completion',
                'note_completion',
                'form_completion',
                'summary_completion'
            )
              AND options_shared IS NOT NULL
            """
        )
    ).mappings().all()

    updated = 0
    for row in rows:
        structure = row["options_shared"]
        if not isinstance(structure, dict):
            continue
        if direction == "up":
            new_structure = _upgrade_structure(structure)
        else:
            new_structure = _downgrade_structure(structure)
        if new_structure is None or new_structure == structure:
            continue
        conn.execute(
            text(
                """
                UPDATE question_groups
                SET options_shared = CAST(:payload AS jsonb)
                WHERE id = CAST(:id AS uuid)
                """
            ),
            {"payload": json.dumps(new_structure), "id": str(row["id"])},
        )
        updated += 1

    logger.info(
        "compound segments migration (%s): updated %s / %s groups",
        direction,
        updated,
        len(rows),
    )


def upgrade() -> None:
    _rewrite_groups("up")


def downgrade() -> None:
    _rewrite_groups("down")
