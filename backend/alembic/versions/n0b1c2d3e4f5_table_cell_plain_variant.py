"""Add variant:plain to existing table cells.

Revision ID: n0b1c2d3e4f5
Revises: m9a0b1c2d3e4
Create Date: 2026-07-11

Table cells gain an explicit cell-level variant:

  { segments: [...] }  ->  { variant: "plain", segments: [...] }

Bullets cells (new capability) are left untouched if already present.

DOWN: strip variant from plain cells. Bullets cells are flattened into a
single segments array (gaps preserved in order); multi-bullet layout is
lost on downgrade.
"""

from __future__ import annotations

import copy
import json
import logging
from typing import Any, Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "n0b1c2d3e4f5"
down_revision: Union[str, None] = "m9a0b1c2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.runtime.migration")


def _upgrade_cell(cell: Any) -> Any:
    if not isinstance(cell, dict):
        return cell
    if cell.get("variant") in ("plain", "bullets"):
        return cell
    # Segments-shaped (post m9a0) or anything with segments → plain
    if "segments" in cell:
        out = copy.deepcopy(cell)
        out["variant"] = "plain"
        return out
    # Legacy type text|gap — leave for runtime normalize; still tag plain
    # only if we can wrap. Prefer leaving legacy alone if no segments yet.
    return cell


def _flatten_bullets(bullets: list[Any]) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for bi, bullet in enumerate(bullets):
        if not isinstance(bullet, dict):
            continue
        segs = bullet.get("segments") or []
        if bi > 0 and segments:
            # Join bullets with " / " text separator on downgrade
            if segments and segments[-1].get("type") == "text":
                segments[-1] = {
                    "type": "text",
                    "value": str(segments[-1].get("value", "")) + " / ",
                }
            else:
                segments.append({"type": "text", "value": " / "})
        for s in segs:
            if isinstance(s, dict):
                segments.append(copy.deepcopy(s))
    if not segments:
        segments = [{"type": "text", "value": ""}]
    return segments


def _downgrade_cell(cell: Any) -> Any:
    if not isinstance(cell, dict):
        return cell
    variant = cell.get("variant")
    if variant == "bullets":
        logger.warning(
            "Downgrade: flattening bullets table cell to plain segments"
        )
        return {"segments": _flatten_bullets(list(cell.get("bullets") or []))}
    if variant == "plain":
        out = copy.deepcopy(cell)
        out.pop("variant", None)
        return out
    return cell


def _rewrite_groups(direction: str) -> None:
    conn = op.get_bind()
    rows = conn.execute(
        text(
            """
            SELECT id, options_shared
            FROM question_groups
            WHERE question_type = 'table_completion'
              AND options_shared IS NOT NULL
            """
        )
    ).mappings().all()

    updated = 0
    for row in rows:
        structure = row["options_shared"]
        if not isinstance(structure, dict) or structure.get("variant") != "table":
            continue
        out = copy.deepcopy(structure)
        rows_data = out.get("rows")
        if not isinstance(rows_data, list):
            continue
        changed = False
        new_rows = []
        for row_cells in rows_data:
            if not isinstance(row_cells, list):
                new_rows.append(row_cells)
                continue
            new_row = []
            for cell in row_cells:
                if direction == "up":
                    next_cell = _upgrade_cell(cell)
                else:
                    next_cell = _downgrade_cell(cell)
                if next_cell != cell:
                    changed = True
                new_row.append(next_cell)
            new_rows.append(new_row)
        if not changed:
            continue
        out["rows"] = new_rows
        conn.execute(
            text(
                """
                UPDATE question_groups
                SET options_shared = CAST(:payload AS jsonb)
                WHERE id = CAST(:id AS uuid)
                """
            ),
            {"payload": json.dumps(out), "id": str(row["id"])},
        )
        updated += 1

    logger.info(
        "table cell variant migration (%s): updated %s / %s groups",
        direction,
        updated,
        len(rows),
    )


def upgrade() -> None:
    _rewrite_groups("up")


def downgrade() -> None:
    _rewrite_groups("down")
