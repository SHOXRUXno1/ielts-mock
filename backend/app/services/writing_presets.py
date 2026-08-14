"""Default IELTS Writing instructions and questions per task/essay type."""

TASK1_DEFAULT_INSTRUCTION = (
    "Summarise the information by selecting and reporting the main features, "
    "and make comparisons where relevant."
)

TASK2_DEFAULT_INSTRUCTIONS: dict[str | None, str] = {
    None: (
        "Give reasons for your answer and include any relevant examples "
        "from your own knowledge or experience."
    ),
    "opinion": (
        "Give reasons for your answer and include any relevant examples "
        "from your own knowledge or experience."
    ),
    "discussion": (
        "Give reasons for your answer and include any relevant examples "
        "from your own knowledge or experience."
    ),
    "problem_solution": (
        "Give reasons for your answer and include any relevant examples "
        "from your own knowledge or experience."
    ),
    "advantages_disadvantages": (
        "Give reasons for your answer and include any relevant examples "
        "from your own knowledge or experience."
    ),
    "double_question": (
        "Give reasons for your answer and include any relevant examples "
        "from your own knowledge or experience."
    ),
}

TASK2_QUESTION_PRESETS: dict[str, str] = {
    "opinion": "To what extent do you agree or disagree with this statement?",
    "discussion": "Discuss both these views and give your own opinion.",
    "problem_solution": "What problems does this cause and what solutions can you suggest?",
    "advantages_disadvantages": "Discuss the advantages and disadvantages.",
    "double_question": "What are the reasons for this? What can be done to address it?",
}

ALL_KNOWN_INSTRUCTIONS = {TASK1_DEFAULT_INSTRUCTION} | set(TASK2_DEFAULT_INSTRUCTIONS.values())
ALL_KNOWN_QUESTIONS = set(TASK2_QUESTION_PRESETS.values())


def get_default_instruction(task_number: int, essay_type: str | None = None) -> str:
    if task_number == 1:
        return TASK1_DEFAULT_INSTRUCTION
    return TASK2_DEFAULT_INSTRUCTIONS.get(essay_type, TASK2_DEFAULT_INSTRUCTIONS[None])


def get_default_question(essay_type: str | None) -> str | None:
    if not essay_type:
        return None
    return TASK2_QUESTION_PRESETS.get(essay_type)
