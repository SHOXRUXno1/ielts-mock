"""Auto-scoring for Reading and Listening sections.

Compares student answers against answer_key, counts correct,
and converts to IELTS band using official conversion tables.

answer_key canonical formats (both legacy seed variants accepted):
  mcq / true_false_ng / yes_no_ng / map_labeling : {"correct": "..."} or {"answer": "..."}
  gap_fill / sentence_completion / short_answer : {"correct": "..." | [...]}
  matching:
    canonical : {"correct": {"item0": "A", "item1": "B", ...}}
    legacy    : {"answers": ["A", "B", ...]}  — paired with content.items order
"""

from types import SimpleNamespace

from app.models.answer import Answer
from app.models.question import Question
from app.services.band_calc import round_ielts_band

# Official IELTS band conversion: correct_answers -> band
# Source: Cambridge IELTS official score charts
LISTENING_BAND_TABLE: list[tuple[int, float]] = [
    (39, 9.0),   # 39-40
    (37, 8.5),   # 37-38
    (35, 8.0),   # 35-36
    (32, 7.5),   # 32-34
    (30, 7.0),   # 30-31
    (26, 6.5),   # 26-29
    (23, 6.0),   # 23-25
    (18, 5.5),   # 18-22
    (16, 5.0),   # 16-17
    (13, 4.5),   # 13-15
    (11, 4.0),   # 11-12
    (8, 3.5),    # 8-10
    (6, 3.0),    # 6-7
    (4, 2.5),    # 4-5
    (2, 2.0),    # 2-3
    (1, 1.0),    # 1
]

READING_ACADEMIC_BAND_TABLE: list[tuple[int, float]] = [
    (39, 9.0),   # 39-40
    (37, 8.5),   # 37-38
    (35, 8.0),   # 35-36
    (33, 7.5),   # 33-34
    (30, 7.0),   # 30-32
    (27, 6.5),   # 27-29
    (23, 6.0),   # 23-26
    (19, 5.5),   # 19-22
    (15, 5.0),   # 15-18
    (13, 4.5),   # 13-14
    (10, 4.0),   # 10-12
    (8, 3.5),    # 8-9
    (6, 3.0),    # 6-7
    (4, 2.5),    # 4-5
    (3, 2.0),    # 3
    (1, 1.0),    # 1-2
]


def _correct_to_band(correct: int, table: list[tuple[int, float]]) -> float:
    for threshold, band in table:
        if correct >= threshold:
            return band
    return 0.0


def correct_to_listening_band(correct: int) -> float:
    return _correct_to_band(correct, LISTENING_BAND_TABLE)


def correct_to_reading_band(correct: int) -> float:
    # TODO: add READING_GENERAL_BAND_TABLE for General Training (deferred; platform is Academic-only for now)
    return _correct_to_band(correct, READING_ACADEMIC_BAND_TABLE)


def compute_writing_band(
    task_1: float | None,
    task_2: float | None,
) -> float | None:
    """IELTS Writing overall: Task 2 is weighted double Task 1.

    writing_band = round_ielts_band((T1 * 1 + T2 * 2) / 3)

    Uses IELTS half-up rounding (6.5 → 7), matching the canonical
    round_ielts_band used everywhere else in the pipeline.

    Returns None if either task band is missing (do not average a single task).
    """
    if task_1 is None or task_2 is None:
        return None
    return round_ielts_band((task_1 * 1 + task_2 * 2) / 3)


def _normalize(text: str) -> str:
    return text.strip().lower()


def _letter_prefix(value: str) -> str:
    """Leading option token of a lettered answer, normalized.

    Map/heading options render to the student as "E. garage" or
    "iii. Some heading", but the answer key stores only the letter ("E",
    "iii"). The frontend can submit either the full option or the bare
    letter, so compare on the token before the first dot.
    """
    v = str(value).strip()
    dot = v.find(".")
    head = v[:dot] if dot > 0 else v
    return _normalize(head)


def scoring_slots_for_question(question: object) -> int:
    """How many IELTS marks / display numbers one Question row contributes.

    multi_select: prefer content.choose_n (students choose N); fall back to
    len(correct list). Scalar correct (legacy pair_id rows) → 1.
    All other types → 1.
    """
    qtype = getattr(question, "question_type", None)
    qtype_str = getattr(qtype, "value", qtype)
    if qtype_str != "multi_select":
        return 1

    content = getattr(question, "content", None) or {}
    if not isinstance(content, dict):
        content = {}
    choose_n = content.get("choose_n")
    if isinstance(choose_n, int) and choose_n >= 1:
        return choose_n

    key = getattr(question, "answer_key", None) or {}
    if not isinstance(key, dict):
        key = {}
    correct = key.get("correct") if "correct" in key else key.get("answer")
    if isinstance(correct, list) and len(correct) > 0:
        return len(correct)

    return 1


def count_questions_in_section(section: object) -> int:
    """Sum scoring slots for all questions in a section."""
    questions = getattr(section, "questions", None) or []
    return sum(scoring_slots_for_question(q) for q in questions)


def assign_groups_slot_numbers(
    groups: list[object],
    base_offset: int = 0,
) -> dict[str, tuple[int, int]]:
    """Inclusive IELTS display numbers across groups in a section.

    Groups sorted by ``order``; questions within each group by ``order``.
    Returns ``{question_id: (start, end)}`` where numbers start at base_offset+1.
    """
    sorted_groups = sorted(
        groups,
        key=lambda g: getattr(g, "order", 0),
    )
    result: dict[str, tuple[int, int]] = {}
    cursor = 1
    for group in sorted_groups:
        qs = sorted(
            getattr(group, "questions", None) or [],
            key=lambda q: getattr(q, "order", 0),
        )
        group_type = getattr(group, "question_type", None)
        for q in qs:
            # Prefer question's own type; fall back to group type for orphans.
            if getattr(q, "question_type", None) is None and group_type is not None:
                q = SimpleNamespace(
                    question_type=group_type,
                    content=getattr(q, "content", None),
                    answer_key=getattr(q, "answer_key", None),
                )
            slots = scoring_slots_for_question(q)
            qid = str(getattr(q, "id", ""))
            if not qid:
                continue
            start = base_offset + cursor
            end = base_offset + cursor + slots - 1
            result[qid] = (start, end)
            cursor += slots
    return result


def _option_aliases(content: dict) -> dict[str, set[str]]:
    """Map each option (and its letter A/B/C…) to a set of equivalent normalized forms."""
    options = content.get("options")
    if not isinstance(options, list):
        return {}
    aliases: dict[str, set[str]] = {}
    for i, opt in enumerate(options):
        letter = chr(65 + i)
        forms = {_normalize(letter), _normalize(str(opt))}
        for f in forms:
            aliases.setdefault(f, set()).update(forms)
    return aliases


def _expand_token(token: str, aliases: dict[str, set[str]]) -> set[str]:
    n = _normalize(token)
    return aliases.get(n, {n})


def _tokens_match(a: str, b: str, aliases: dict[str, set[str]]) -> bool:
    return bool(_expand_token(a, aliases) & _expand_token(b, aliases))


def check_text_answer(
    student: str,
    correct_variants: "str | list[str]",
    max_words: "int | None" = None,
    case_sensitive: bool = False,
) -> bool:
    """Compare a free-text student answer against one or more correct variants.

    - Normalises both sides (strip; lowercase unless case_sensitive).
    - Accepts a single string or a list of acceptable strings for *correct_variants*.
    - A match against an accepted variant always counts as correct (even if the
      variant is longer than *max_words* — e.g. ``115`` / ``one hundred fifteen``).
    - *max_words* only rejects answers that do **not** match any variant.
    """
    student_raw = str(student).strip()
    student_norm = student_raw if case_sensitive else student_raw.lower()
    if isinstance(correct_variants, str):
        correct_variants = [correct_variants]
    for v in correct_variants:
        candidate = str(v).strip()
        if not case_sensitive:
            candidate = candidate.lower()
        if candidate == student_norm:
            return True
    if max_words is not None and len(student_raw.split()) > max_words:
        return False
    return False


def _get_correct_scalar(answer_key: dict) -> str:
    """Read correct answer from either canonical 'correct' or legacy 'answer' key."""
    v = answer_key.get("correct") or answer_key.get("answer") or ""
    return str(v)


def _matching_pairs(question: Question) -> dict[str, str]:
    """Return the canonical correct-pairs dict for matching/map_labeling.

    Supports two answer_key formats:
      canonical : {"correct": {"Climate data is unreliable": "A", ...}}
      legacy    : {"answers": ["A", "B", ...]} paired with content.items order
    """
    ak = question.answer_key or {}
    content = question.content or {}

    # Canonical dict form
    if "correct" in ak and isinstance(ak["correct"], dict):
        return {str(k): str(v) for k, v in ak["correct"].items()}

    # Legacy positional-array form: {"answers": ["A","B","C"]}
    if "answers" in ak and isinstance(ak["answers"], list):
        # items in content may be stored as "items" or "left"
        items: list = content.get("items") or content.get("left") or []
        return {str(item): str(ans) for item, ans in zip(items, ak["answers"])}

    # Dict stored under "answer" key
    if "answer" in ak and isinstance(ak["answer"], dict):
        return {str(k): str(v) for k, v in ak["answer"].items()}

    return {}


def score_answer(question: Question, answer: Answer) -> tuple[int, int]:
    """Score a single answer, returning (correct_sub_items, total_sub_items).

    For most types this is (1, 1) or (0, 1).
    For matching each pair counts as its own sub-item so a question with
    5 pairs contributes up to 5 correct points.
    Updates answer.is_correct and answer.score in-place (not committed).
    """
    if question.answer_key is None:
        answer.is_correct = False
        answer.score = 0.0
        return 0, 1

    response = answer.response or {}
    student_value = response.get("answer", "")
    qtype = question.question_type

    if qtype in ("essay", "speaking_part"):
        return 0, 0

    if qtype in ("mcq", "true_false_ng", "yes_no_ng"):
        correct = _get_correct_scalar(question.answer_key)
        is_correct = _normalize(str(student_value)) == _normalize(correct)
        answer.is_correct = is_correct
        answer.score = 1.0 if is_correct else 0.0
        return (1, 1) if is_correct else (0, 1)

    if qtype in (
        "gap_fill",
        "sentence_completion",
        "short_answer",
        "table_completion",
        "note_completion",
        "form_completion",
        "summary_completion",
        "flow_chart_completion",
        "diagram_labeling",
    ):
        ak = question.answer_key or {}
        correct_variants = ak.get("correct", [])
        content = question.content or {}
        max_words: int | None = None
        raw_mw = ak.get("max_words")
        if raw_mw is None and qtype in ("sentence_completion", "short_answer"):
            raw_mw = content.get("max_words")
        if raw_mw is not None:
            try:
                max_words = int(raw_mw)
            except (ValueError, TypeError):
                max_words = None
        case_sensitive = bool(ak.get("case_sensitive", False))
        is_correct = check_text_answer(
            str(student_value),
            correct_variants,
            max_words,
            case_sensitive=case_sensitive,
        )
        answer.is_correct = is_correct
        answer.score = 1.0 if is_correct else 0.0
        return (1, 1) if is_correct else (0, 1)

    if qtype == "multi_select":
        # List correct → N marks with partial credit (intersection).
        # Scalar correct (legacy pair_id row) → 1 mark if letter appears in student list.
        ak = question.answer_key or {}
        content = question.content or {}
        aliases = _option_aliases(content if isinstance(content, dict) else {})
        raw_correct = ak.get("correct") if "correct" in ak else ak.get("answer")
        student_list: list = student_value if isinstance(student_value, list) else []

        if isinstance(raw_correct, list) and len(raw_correct) > 0:
            total = len(raw_correct)
            # Count how many correct answers the student selected (extras don't cancel).
            hits = 0
            used_student: set[int] = set()
            for correct_item in raw_correct:
                for si, student_item in enumerate(student_list):
                    if si in used_student:
                        continue
                    if _tokens_match(str(correct_item), str(student_item), aliases):
                        hits += 1
                        used_student.add(si)
                        break
            correct_count = min(hits, total)
            answer.is_correct = correct_count == total
            answer.score = correct_count / total if total else 0.0
            return correct_count, total

        # Scalar / single-string correct (legacy pair row)
        correct_scalar = str(raw_correct or "")
        matched = any(
            _tokens_match(correct_scalar, str(s), aliases) for s in student_list
        )
        answer.is_correct = matched
        answer.score = 1.0 if matched else 0.0
        return (1, 1) if matched else (0, 1)

    if qtype in ("matching_headings", "matching_information", "matching_features", "map_labeling"):
        correct = _get_correct_scalar(question.answer_key)
        # Options live on the group, not the question, so match on the letter
        # token: the key is "E"/"iii" while the student may submit "E. garage".
        is_correct = (
            _normalize(str(student_value)) == _normalize(correct)
            or _letter_prefix(student_value) == _letter_prefix(correct)
        )
        answer.is_correct = is_correct
        answer.score = 1.0 if is_correct else 0.0
        return (1, 1) if is_correct else (0, 1)

    if qtype == "matching":
        correct_pairs = _matching_pairs(question)

        # One item per row — "Gen" against a key of "A" — which is how the
        # editor writes matching now, and how every sibling matching type is
        # already scored. There are no pairs to walk here, and the pair branch
        # below reads the absence of them as nothing correct, so the question
        # could not be answered at all: nine of them across Cambridge IELTS 9
        # Test 4 had never once been marked right.
        if not correct_pairs:
            correct = _get_correct_scalar(question.answer_key)
            is_correct = bool(correct) and _normalize(str(student_value)) == _normalize(correct)
            answer.is_correct = is_correct
            answer.score = 1.0 if is_correct else 0.0
            return (1, 1) if is_correct else (0, 1)

        total_pairs = max(len(correct_pairs), 1)

        if isinstance(student_value, dict) and correct_pairs:
            correct_count = sum(
                1 for k, v in correct_pairs.items()
                if _normalize(str(student_value.get(k, ""))) == _normalize(v)
            )
        else:
            correct_count = 0

        answer.is_correct = correct_count == total_pairs
        answer.score = correct_count / total_pairs
        return correct_count, total_pairs

    # Unknown type — no score
    answer.is_correct = False
    answer.score = 0.0
    return 0, 1


def check_answer(question: Question, answer: Answer) -> bool:
    """Check a single answer. Returns True if fully correct.

    Kept for backwards compatibility; internally uses score_answer.
    """
    correct, total = score_answer(question, answer)
    return total > 0 and correct == total


def _question_item_total(question: Question) -> int:
    """How many scoreable sub-items a question contributes when unanswered."""
    qtype = question.question_type
    if qtype in ("essay", "speaking_part"):
        return 0
    if qtype == "matching":
        return max(len(_matching_pairs(question)), 1)
    if qtype == "multi_select":
        return scoring_slots_for_question(question)
    return 1


def score_section(questions: list[Question], answers: list[Answer]) -> tuple[int, int]:
    """Score all questions in a section.

    Returns (correct_sub_items, total_sub_items).
    Matching questions contribute one sub-item per pair, not one per row.
    Unanswered questions count as wrong and still add to the total (so a
    section with 40 questions always has total 40, not ``len(answers)``).
    """
    ans_by_q = {a.question_id: a for a in answers}
    correct_total = 0
    items_total = 0

    for q in questions:
        if q.question_type in ("essay", "speaking_part"):
            continue
        ans = ans_by_q.get(q.id)
        if ans is None:
            items_total += _question_item_total(q)
            continue
        c, t = score_answer(q, ans)
        correct_total += c
        items_total += t

    return correct_total, items_total
