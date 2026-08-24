"""Build a printable IELTS score-report context and render it to PDF."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.services.scoring import scoring_slots_for_question

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

NO_ANSWER = "(no answer)"

OUTCOME_LABELS: dict[str, str] = {
    "correct": "Correct",
    "partial": "Partly correct",
    "incorrect": "Incorrect",
    "skipped": "Skipped",
}

STATUS_LABELS: dict[str, str] = {
    "fully_scored": "Fully scored",
    "auto_scored": "Auto scored",
    "scored": "Auto scored",
    "speaking_in_progress": "Speaking in progress",
    "completed_without_speaking": "Completed (no speaking)",
    "partial": "Partial",
    "completed": "Scoring writing",
    "abandoned": "Abandoned",
    "in_progress": "In Progress",
}

SKILL_ROWS: tuple[tuple[str, str, str, str | None], ...] = (
    ("listening", "Listening", "listening_band", "listening_raw"),
    ("reading", "Reading", "reading_band", "reading_raw"),
    ("writing", "Writing", "writing_band", None),
    ("speaking", "Speaking", "speaking_band", None),
)

WRITING_TASK1_CRITERIA: tuple[tuple[str, str], ...] = (
    ("task_achievement", "Task Achievement"),
    ("coherence_cohesion", "Coherence & Cohesion"),
    ("lexical_resource", "Lexical Resource"),
    ("grammatical_range", "Grammatical Range"),
)

WRITING_TASK2_CRITERIA: tuple[tuple[str, str], ...] = (
    ("task_response", "Task Response"),
    ("coherence_cohesion", "Coherence & Cohesion"),
    ("lexical_resource", "Lexical Resource"),
    ("grammatical_range", "Grammatical Range"),
)

SPEAKING_CRITERIA: tuple[tuple[str, str], ...] = (
    ("fluency_coherence", "Fluency & Coherence"),
    ("lexical_resource", "Lexical Resource"),
    ("grammatical_range", "Grammar"),
    ("pronunciation", "Pronunciation"),
)

_DESCRIPTORS: tuple[tuple[float, str], ...] = (
    (9, "Expert"),
    (8, "Very good"),
    (7, "Good"),
    (6, "Competent"),
    (5, "Modest"),
    (4, "Limited"),
)

_jinja_env: Environment | None = None


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def band_descriptor(band: float | None) -> str | None:
    if band is None:
        return None
    for minimum, label in _DESCRIPTORS:
        if band >= minimum:
            return label
    return "Limited"


def cefr_level(band: float | None) -> str | None:
    if band is None:
        return None
    if band >= 8.5:
        return "C2"
    if band >= 7:
        return "C1"
    if band >= 5.5:
        return "B2"
    if band >= 4:
        return "B1"
    return "A2"


def format_band(band: Any) -> str:
    if band is None:
        return "—"
    try:
        return f"{float(band):.1f}"
    except (TypeError, ValueError):
        return "—"


def format_student_answer(response: dict[str, Any] | None) -> str:
    if not response:
        return NO_ANSWER
    val = response.get("answer")
    if val is None or val == "":
        return NO_ANSWER
    if isinstance(val, list):
        return ", ".join(str(item) for item in val)
    if isinstance(val, dict):
        return "; ".join(f"{key} → {value}" for key, value in val.items())
    return str(val)


def format_correct_answer(answer_key: dict[str, Any] | None) -> str:
    if not answer_key:
        return ""
    accepted = answer_key.get("accepted_answers")
    if isinstance(accepted, list) and accepted:
        return " | ".join(str(item) for item in accepted)
    correct = answer_key.get("correct", answer_key.get("answer"))
    if correct is None:
        legacy = answer_key.get("answers")
        if isinstance(legacy, list) and legacy:
            return " | ".join(str(item) for item in legacy)
        return ""
    if isinstance(correct, list):
        sorted_vals = sorted((str(item) for item in correct))
        return " | ".join(sorted_vals) if sorted_vals else ""
    if isinstance(correct, dict):
        return " | ".join(str(value) for value in correct.values())
    return str(correct)


def format_answer_set(items: Any) -> str:
    """Join options that must *all* be given, sorted, e.g. ``B, D``.

    Deliberately a comma, to keep it apart from the ``|`` used for alternatives
    where any one is accepted. Both columns are sorted the same way so the
    candidate's answer and the key can be compared letter for letter.
    """
    if not isinstance(items, list):
        return ""
    return ", ".join(sorted(str(item) for item in items if str(item)))


def answer_marks(answer: Any) -> tuple[int, int]:
    """Marks earned and marks available for one answer row.

    "Choose TWO letters" occupies two question numbers and is worth two marks,
    so one right letter earns one of them — which is what the band already
    reflects. ``is_correct`` is all-or-nothing and cannot show that, so the
    earned share is read from ``score``.
    """
    question = _get(answer, "question")
    total = 1
    if question is not None:
        total = scoring_slots_for_question(
            SimpleNamespace(
                question_type=_get(question, "question_type"),
                content=_get(question, "content"),
                answer_key=_get(question, "answer_key"),
            )
        )

    fully_correct = _get(answer, "is_correct") is True
    if total <= 1:
        return (1, 1) if fully_correct else (0, 1)
    if fully_correct:
        return total, total

    try:
        fraction = float(_get(answer, "score") or 0.0)
    except (TypeError, ValueError):
        fraction = 0.0
    earned = round(fraction * total)
    return max(0, min(total - 1, earned)), total


def answer_outcome(answer: Any) -> str:
    student = format_student_answer(_get(answer, "response") or {})
    if student == NO_ANSWER:
        return "skipped"
    if _get(answer, "is_correct") is True:
        return "correct"
    earned, _total = answer_marks(answer)
    return "partial" if earned > 0 else "incorrect"


def display_number(question: Any) -> str:
    if question is None:
        return "?"
    start = _get(question, "computed_number")
    end = _get(question, "computed_number_end")
    if isinstance(start, int) and start >= 1:
        if isinstance(end, int) and end != start:
            return f"{start}–{end}"
        return str(start)
    order = _get(question, "order")
    return str(order) if order is not None else "?"


def format_report_date(value: datetime | None) -> str:
    if value is None:
        return "—"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.strftime("%d %b %Y, %H:%M")


def format_duration(started: datetime | None, finished: datetime | None) -> str:
    if started is None or finished is None:
        return "—"
    minutes = round((finished - started).total_seconds() / 60)
    if minutes < 1:
        return "< 1 min"
    return f"{minutes} min"


def status_label(status: str | None) -> str:
    if not status:
        return "In Progress"
    return STATUS_LABELS.get(status, status.replace("_", " ").title())


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _sort_key(number: str) -> tuple[int, int]:
    digits = []
    current = ""
    for char in number:
        if char.isdigit():
            current += char
        elif current:
            digits.append(int(current))
            current = ""
    if current:
        digits.append(int(current))
    if not digits:
        return (999, 999)
    if len(digits) == 1:
        return (digits[0], digits[0])
    return (digits[0], digits[1])


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item]


def _criterion(data: dict[str, Any], key: str, label: str, fallback: str | None = None) -> dict[str, Any] | None:
    raw = data.get(key)
    if not isinstance(raw, dict) and fallback:
        raw = data.get(fallback)
    if not isinstance(raw, dict):
        return None
    return {
        "label": label,
        "band": raw.get("band"),
        "band_label": format_band(raw.get("band")),
        "feedback": str(raw.get("feedback") or ""),
    }


def _objective_groups(answers: list[Any], skill: str) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for answer in answers:
        section = _get(answer, "section")
        if _get(section, "type") != skill:
            continue
        section_id = str(_get(section, "id") or "unknown")
        bucket = grouped.setdefault(
            section_id,
            {"order": _get(section, "order") or 999, "answers": []},
        )
        bucket["answers"].append(answer)

    prefix = "Part" if skill == "listening" else "Passage"
    groups: list[dict[str, Any]] = []
    for bucket in sorted(grouped.values(), key=lambda item: item["order"]):
        rows = []
        for answer in bucket["answers"]:
            question = _get(answer, "question")
            answer_key = _get(question, "answer_key") if question is not None else None
            response = _get(answer, "response") or {}
            earned, total = answer_marks(answer)
            outcome = answer_outcome(answer)

            student = format_student_answer(response)
            correct = format_correct_answer(answer_key)
            if total > 1:
                # A set of options, not a list of alternatives — show both
                # columns the same way so "Correct" is self-evident.
                picked = format_answer_set(response.get("answer") if isinstance(response, dict) else None)
                student = picked or student
                expected = answer_key.get("correct", answer_key.get("answer")) if isinstance(answer_key, dict) else None
                correct = format_answer_set(expected) or correct

            rows.append(
                {
                    "number": display_number(question),
                    "student": student,
                    "correct": correct,
                    "outcome": outcome,
                    "result_label": OUTCOME_LABELS.get(outcome, outcome),
                    "earned": earned,
                    "total": total,
                    "marks_label": f"{earned}/{total} marks" if total > 1 else "",
                }
            )
        rows.sort(key=lambda row: _sort_key(row["number"]))
        groups.append(
            {
                "label": f"{prefix} {bucket['order']}",
                "rows": rows,
                # Counted in marks, not rows, so the totals match the raw score:
                # a half-right pair adds one mark to each side.
                "correct": sum(row["earned"] for row in rows),
                "incorrect": sum(
                    row["total"] - row["earned"]
                    for row in rows
                    if row["outcome"] != "skipped"
                ),
                "skipped": sum(
                    row["total"] - row["earned"]
                    for row in rows
                    if row["outcome"] == "skipped"
                ),
            }
        )
    return groups


def _writing_section(jobs: list[Any]) -> dict[str, Any]:
    writing_jobs = [job for job in jobs if _get(job, "section_type") == "writing"]
    done = next((job for job in writing_jobs if _get(job, "status") == "done"), None)
    job = done or (writing_jobs[0] if writing_jobs else None)
    if job is None:
        return {"ready": False, "state": "not_attempted", "tasks": []}
    if _get(job, "status") != "done":
        return {"ready": False, "state": "scoring", "tasks": []}

    result = _get(job, "result") or {}
    tasks = result.get("tasks") if isinstance(result, dict) else {}
    if not isinstance(tasks, dict):
        tasks = {}

    out: list[dict[str, Any]] = []
    specs = (
        ("task_1", "Task 1", WRITING_TASK1_CRITERIA, None),
        ("task_2", "Task 2", WRITING_TASK2_CRITERIA, "task_achievement"),
    )
    for key, title, criteria, fallback in specs:
        data = tasks.get(key)
        if not isinstance(data, dict):
            continue
        extracted = []
        for criterion_key, label in criteria:
            item = _criterion(
                data,
                criterion_key,
                label,
                fallback if criterion_key == "task_response" else None,
            )
            if item:
                extracted.append(item)
        out.append(
            {
                "title": title,
                "band": data.get("overall_band"),
                "band_label": format_band(data.get("overall_band")),
                "word_count": data.get("word_count"),
                "criteria": extracted,
                "strengths": _string_list(data.get("strengths")),
                "improvements": _string_list(data.get("improvements")),
                "essay": str(data.get("text") or ""),
            }
        )
    return {
        "ready": bool(out),
        "state": "ready" if out else "not_attempted",
        "tasks": out,
    }


def _speaking_section(jobs: list[Any], session: Any, speaking_band: Any) -> dict[str, Any]:
    speaking_jobs = [job for job in jobs if _get(job, "section_type") == "speaking"]
    done = next((job for job in speaking_jobs if _get(job, "status") == "done"), None)
    job = done or (speaking_jobs[0] if speaking_jobs else None)

    data: dict[str, Any] | None = None
    if job is not None and _get(job, "status") == "done":
        raw = _get(job, "result")
        data = raw if isinstance(raw, dict) else {}
    elif session is not None:
        raw = _get(session, "score_json")
        data = raw if isinstance(raw, dict) else None

    if not data and speaking_band is None:
        if job is not None and _get(job, "status") in ("pending", "processing"):
            return {"ready": False, "state": "scoring"}
        return {"ready": False, "state": "not_attempted"}

    payload = data or {}
    band = speaking_band
    if band is None and job is not None:
        band = _get(job, "band_score")
    if band is None and session is not None:
        band = _get(session, "overall_band")

    criteria = []
    for key, label in SPEAKING_CRITERIA:
        item = _criterion(payload, key, label)
        if item:
            criteria.append(item)

    return {
        "ready": True,
        "state": "ready",
        "band": band,
        "band_label": format_band(band),
        "criteria": criteria,
        "strengths": _string_list(payload.get("strengths")),
        "improvements": _string_list(payload.get("improvements")),
        "transcript": str(payload.get("transcript") or ""),
    }


def build_report_context(detail: Any, student_name: str) -> dict[str, Any]:
    started = _as_datetime(_get(detail, "started_at"))
    finished = _as_datetime(_get(detail, "finished_at"))
    overall = _get(detail, "overall_band")
    answers = list(_get(detail, "answers") or [])
    jobs = list(_get(detail, "evaluation_jobs") or [])
    session = _get(detail, "speaking_session")

    skills = []
    for key, label, band_field, raw_field in SKILL_ROWS:
        band = _get(detail, band_field)
        raw = _get(detail, raw_field) if raw_field else None
        skills.append(
            {
                "key": key,
                "label": label,
                "band": band,
                "band_label": format_band(band),
                "raw": raw,
                "cefr": cefr_level(band),
                "descriptor": band_descriptor(band),
            }
        )

    listening = _objective_groups(answers, "listening")
    reading = _objective_groups(answers, "reading")

    return {
        "student_name": student_name or "Student",
        "test_title": _get(detail, "test_title") or "IELTS Mock Test",
        "status": status_label(_get(detail, "status")),
        "started": format_report_date(started),
        "finished": format_report_date(finished),
        "duration": format_duration(started, finished),
        "generated_at": format_report_date(datetime.now(timezone.utc)),
        "overall": {
            "band": overall,
            "band_label": format_band(overall),
            "descriptor": band_descriptor(overall),
            "cefr": cefr_level(overall),
        },
        "skills": skills,
        "listening": listening,
        "reading": reading,
        "writing": _writing_section(jobs),
        "speaking": _speaking_section(jobs, session, _get(detail, "speaking_band")),
    }


def report_filenames(detail: Any) -> tuple[str, str]:
    finished = _as_datetime(_get(detail, "finished_at")) or _as_datetime(
        _get(detail, "created_at")
    )
    date = finished.strftime("%Y-%m-%d") if finished else "result"
    ascii_name = f"ielts-result-{date}.pdf"
    title = str(_get(detail, "test_title") or "IELTS Mock")
    cleaned = "".join(char if char.isalnum() or char in " -_" else " " for char in title)
    cleaned = " ".join(cleaned.split())[:80] or "IELTS Mock"
    utf8_name = f"IELTS Result - {cleaned} - {date}.pdf"
    return ascii_name, utf8_name


def content_disposition(ascii_name: str, utf8_name: str) -> str:
    return f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{quote(utf8_name)}'


def _environment() -> Environment:
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        _jinja_env.filters["band"] = format_band
    return _jinja_env


def render_report_html(context: dict[str, Any]) -> str:
    return _environment().get_template("result_report.html").render(**context)


def render_report_pdf(context: dict[str, Any]) -> bytes:
    from weasyprint import HTML

    html = render_report_html(context)
    return HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()
