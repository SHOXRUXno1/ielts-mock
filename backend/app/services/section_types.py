"""Section ↔ question-type mapping per IELTS standards."""

READING_TYPES: frozenset[str] = frozenset({
    "mcq", "multi_select", "matching", "matching_information", "matching_features",
    "matching_headings", "true_false_ng", "yes_no_ng", "sentence_completion",
    "short_answer", "summary_completion", "gap_fill", "note_completion", "table_completion",
    "diagram_labeling",
})

LISTENING_TYPES: frozenset[str] = frozenset({
    "mcq", "multi_select", "matching", "matching_features", "map_labeling",
    "form_completion", "note_completion", "table_completion", "summary_completion",
    "sentence_completion", "short_answer", "gap_fill", "flow_chart_completion",
    "diagram_labeling",
})

SECTION_QUESTION_TYPES: dict[str, frozenset[str]] = {
    "reading": READING_TYPES,
    "listening": LISTENING_TYPES,
}


def is_type_allowed(section_type: str, qtype: str) -> bool:
    allowed = SECTION_QUESTION_TYPES.get(section_type)
    return allowed is None or qtype in allowed
