"""Recalc writing bands (IELTS weighted) and remap EvaluationJob task keys.

Revision ID: g3a4b5c6d7e8
Revises: f2a3b4c5d6e7
Create Date: 2026-07-09

Data-only migration:
1. Remap input_data / result.tasks keys from order-based (task_8, …) to task_1/task_2
   using questions.task_number (fallback: prompt text match).
2. Recompute evaluation_jobs.band_score with IELTS formula:
   round((T1*1 + T2*2)/3 * 2)/2 ; NULL if either task missing.
3. Update attempts.writing_band (respect teacher_override_band) and overall_band.

Downgrade is a no-op (cannot restore previous mean-based bands reliably).
"""

from __future__ import annotations

import json
from typing import Any, Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "g3a4b5c6d7e8"
down_revision: Union[str, None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _compute_writing_band(t1: float | None, t2: float | None) -> float | None:
    if t1 is None or t2 is None:
        return None
    return round((t1 * 1 + t2 * 2) / 3 * 2) / 2


def _compute_overall(bands: list[float | None]) -> float | None:
    positive = [b for b in bands if b is not None and b > 0]
    if not positive:
        return None
    return round(sum(positive) / len(positive) * 2) / 2


def _remap_dict(d: dict | None, key_map: dict[str, str]) -> dict:
    if not isinstance(d, dict):
        return {}
    out: dict[str, Any] = {}
    for k, v in d.items():
        out[key_map.get(k, k)] = v
    return out


def upgrade() -> None:
    conn = op.get_bind()

    jobs = conn.execute(
        text(
            """
            SELECT ej.id, ej.attempt_id, ej.input_data, ej.result,
                   ej.band_score, ej.teacher_override_band
            FROM evaluation_jobs ej
            WHERE ej.section_type = 'writing'
            """
        )
    ).mappings().all()

    for job in jobs:
        job_id = job["id"]
        attempt_id = job["attempt_id"]
        input_data = job["input_data"] or {}
        result = job["result"] or {}
        if isinstance(input_data, str):
            input_data = json.loads(input_data)
        if isinstance(result, str):
            result = json.loads(result)

        # Build order/prompt → task_number map from writing questions of this attempt's test
        qrows = conn.execute(
            text(
                """
                SELECT q.order, q.task_number, q.content
                FROM questions q
                JOIN sections s ON s.id = q.section_id
                JOIN attempts a ON a.test_id = s.test_id
                WHERE a.id = :attempt_id
                  AND s.type = 'writing'
                  AND q.question_type = 'essay'
                """
            ),
            {"attempt_id": attempt_id},
        ).mappings().all()

        order_to_tn: dict[int, int] = {}
        prompt_to_tn: dict[str, int] = {}
        for q in qrows:
            tn = q["task_number"]
            if tn not in (1, 2):
                tn = q["order"] if q["order"] in (1, 2) else None
            if tn is None:
                continue
            order_to_tn[int(q["order"])] = int(tn)
            content = q["content"] or {}
            if isinstance(content, str):
                content = json.loads(content)
            prompt = (content.get("prompt") or "").strip()
            if prompt:
                prompt_to_tn[prompt] = int(tn)

        def resolve_key(old_key: str, prompts_dict: dict | None = None) -> str:
            if old_key in ("task_1", "task_2"):
                return old_key
            # Extract numeric suffix
            suffix = old_key.split("_")[-1] if "_" in old_key else ""
            try:
                n = int(suffix)
            except ValueError:
                n = None
            if n is not None and n in order_to_tn:
                return f"task_{order_to_tn[n]}"
            # Prompt-text fallback
            if prompts_dict and old_key in prompts_dict:
                p = str(prompts_dict.get(old_key) or "").strip()
                if p in prompt_to_tn:
                    return f"task_{prompt_to_tn[p]}"
            return old_key

        prompts_src = (input_data.get("prompts") or {}) if isinstance(input_data, dict) else {}
        all_keys: set[str] = set()
        for section_key in ("answers", "prompts", "images", "essay_types"):
            part = input_data.get(section_key) if isinstance(input_data, dict) else None
            if isinstance(part, dict):
                all_keys.update(part.keys())
        tasks = result.get("tasks") if isinstance(result, dict) else None
        if isinstance(tasks, dict):
            all_keys.update(tasks.keys())

        key_map = {k: resolve_key(k, prompts_src) for k in all_keys}
        needs_remap = any(k != v for k, v in key_map.items())

        if needs_remap and isinstance(input_data, dict):
            for section_key in ("answers", "prompts", "images", "essay_types"):
                if isinstance(input_data.get(section_key), dict):
                    input_data[section_key] = _remap_dict(input_data[section_key], key_map)
            conn.execute(
                text(
                    "UPDATE evaluation_jobs SET input_data = CAST(:data AS jsonb) WHERE id = :id"
                ),
                {"data": json.dumps(input_data), "id": job_id},
            )

        if needs_remap and isinstance(result, dict) and isinstance(result.get("tasks"), dict):
            result["tasks"] = _remap_dict(result["tasks"], key_map)

        # Recompute band from task overalls
        tasks_data = (result.get("tasks") or {}) if isinstance(result, dict) else {}
        t1 = (tasks_data.get("task_1") or {}).get("overall_band")
        t2 = (tasks_data.get("task_2") or {}).get("overall_band")
        t1_f = float(t1) if t1 is not None else None
        t2_f = float(t2) if t2 is not None else None
        weighted = _compute_writing_band(t1_f, t2_f)

        if isinstance(result, dict):
            result["overall_band"] = weighted
            conn.execute(
                text(
                    "UPDATE evaluation_jobs SET result = CAST(:data AS jsonb), band_score = :band WHERE id = :id"
                ),
                {"data": json.dumps(result), "id": job_id, "band": weighted},
            )
        else:
            conn.execute(
                text("UPDATE evaluation_jobs SET band_score = :band WHERE id = :id"),
                {"band": weighted, "id": job_id},
            )

        # Update attempt writing_band / overall_band
        attempt = conn.execute(
            text(
                """
                SELECT writing_band, listening_band, reading_band, speaking_band
                FROM attempts WHERE id = :id
                """
            ),
            {"id": attempt_id},
        ).mappings().first()
        if attempt is None:
            continue

        override = job["teacher_override_band"]
        new_writing = float(override) if override is not None else weighted
        overall = _compute_overall(
            [
                attempt["listening_band"],
                attempt["reading_band"],
                new_writing,
                attempt["speaking_band"],
            ]
        )
        conn.execute(
            text(
                """
                UPDATE attempts
                SET writing_band = :wb, overall_band = :ob
                WHERE id = :id
                """
            ),
            {"wb": new_writing, "ob": overall, "id": attempt_id},
        )


def downgrade() -> None:
    # Data-only migration — previous mean-based bands cannot be restored reliably.
    pass
