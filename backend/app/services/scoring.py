"""Auto-scoring for Reading and Listening sections.

Compares student answers against answer_key, counts correct,
and converts to IELTS band using official conversion tables.

answer_key canonical formats (both legacy seed variants accepted):
  mcq / true_false_ng / yes_no_ng : {"correct": "..."} or {"answer": "..."}
  gap_fill / sentence_completion / short_answer : {"correct": "..." | [...]}
  matching / map_labeling:
    canonical : {"correct": {"item0": "A", "item1": "B", ...}}
    legacy    : {"answers": ["A", "B", ...]}  — paired with content.items order
"""

from app.models.answer import Answer
from app.models.question import Question

# Official IELTS band conversion: correct_answers -> band
# Source: Cambridge IELTS official score charts
LISTENING_BAND_TABLE: list[tuple[int, float]] = [
    (40, 9.0), (39, 8.5),
    (37, 8.0), (35, 7.5),
    (32, 7.0), (30, 6.5),
    (26, 6.0), (23, 5.5),
    (18, 5.0), (16, 4.5),
    (13, 4.0), (10, 3.5),
    (6, 3.0), (4, 2.5),
    (2, 2.0), (1, 1.0),
]

READING_ACADEMIC_BAND_TABLE: list[tuple[int, float]] = [
    (40, 9.0), (39, 8.5),
    (37, 8.0), (35, 7.5),
    (33, 7.0), (30, 6.5),
    (27, 6.0), (23, 5.5),
    (19, 5.0), (15, 4.5),
    (13, 4.0), (10, 3.5),
    (8, 3.0), (6, 2.5),
    (4, 2.0), (3, 1.0),
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


def _normalize(text: str) -> str:
    return text.strip().lower()


def check_text_answer(
    student: str,
    correct_variants: "str | list[str]",
    max_words: "int | None" = None,
) -> bool:
    """Compare a free-text student answer against one or more correct variants.

    - Normalises both sides (strip + lowercase).
    - If *max_words* is set, answers exceeding that word count are marked wrong.
    - Accepts a single string or a list of acceptable strings for *correct_variants*.
    """
    student_norm = _normalize(str(student))
    if max_words is not None and len(student_norm.split()) > max_words:
        return False
    if isinstance(correct_variants, str):
        correct_variants = [correct_variants]
    return any(_normalize(str(v)) == student_norm for v in correct_variants)


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
    For matching/map_labeling each pair counts as its own sub-item so a
    question with 5 pairs contributes up to 5 correct points — matching
    real IELTS scoring where each gap/match = 1 mark.
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

    if qtype in ("gap_fill", "sentence_completion", "short_answer"):
        ak = question.answer_key or {}
        correct_variants = ak.get("correct", [])
        content = question.content or {}
        max_words: int | None = None
        if qtype in ("sentence_completion", "short_answer"):
            raw_mw = content.get("max_words")
            if raw_mw is not None:
                try:
                    max_words = int(raw_mw)
                except (ValueError, TypeError):
                    max_words = None
        is_correct = check_text_answer(str(student_value), correct_variants, max_words)
        answer.is_correct = is_correct
        answer.score = 1.0 if is_correct else 0.0
        return (1, 1) if is_correct else (0, 1)

    if qtype == "multi_select":
        # answer_key.correct may be a list (e.g. ["A","C"]) or a single string.
        # Score 1.0 only if the student selected exactly the right set of answers.
        raw_correct = question.answer_key.get("correct") or question.answer_key.get("answer") or []
        if isinstance(raw_correct, list):
            correct_set = {_normalize(str(v)) for v in raw_correct}
        else:
            correct_set = {_normalize(str(raw_correct))}

        student_list: list = student_value if isinstance(student_value, list) else []
        student_set = {_normalize(str(v)) for v in student_list}

        is_correct = student_set == correct_set
        answer.is_correct = is_correct
        answer.score = 1.0 if is_correct else 0.0
        return (1, 1) if is_correct else (0, 1)

    if qtype in ("matching_headings", "matching_information", "matching_features"):
        correct = _get_correct_scalar(question.answer_key)
        is_correct = _normalize(str(student_value)) == _normalize(correct)
        answer.is_correct = is_correct
        answer.score = 1.0 if is_correct else 0.0
        return (1, 1) if is_correct else (0, 1)

    if qtype in ("matching", "map_labeling"):
        correct_pairs = _matching_pairs(question)
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


def score_section(questions: list[Question], answers: list[Answer]) -> tuple[int, int]:
    """Score all answers for a section.

    Returns (correct_sub_items, total_sub_items).
    Matching questions contribute one sub-item per pair, not one per row.
    """
    q_map = {q.id: q for q in questions}
    correct_total = 0
    items_total = 0

    for ans in answers:
        q = q_map.get(ans.question_id)
        if q is None:
            continue
        if q.question_type in ("essay", "speaking_part"):
            continue
        c, t = score_answer(q, ans)
        correct_total += c
        items_total += t

    return correct_total, items_total
