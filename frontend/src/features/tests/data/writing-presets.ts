export const TASK1_DEFAULT_INSTRUCTION =
  'Summarise the information by selecting and reporting the main features, and make comparisons where relevant.'

export const TASK2_DEFAULT_INSTRUCTIONS: Record<string, string> = {
  __default__:
    'Give reasons for your answer and include any relevant examples from your own knowledge or experience.',
  opinion:
    'Give reasons for your answer and include any relevant examples from your own knowledge or experience.',
  discussion:
    'Give reasons for your answer and include any relevant examples from your own knowledge or experience.',
  problem_solution:
    'Give reasons for your answer and include any relevant examples from your own knowledge or experience.',
  advantages_disadvantages:
    'Give reasons for your answer and include any relevant examples from your own knowledge or experience.',
  double_question:
    'Give reasons for your answer and include any relevant examples from your own knowledge or experience.',
}

export const TASK2_QUESTION_PRESETS: Record<string, string> = {
  opinion: 'To what extent do you agree or disagree with this statement?',
  discussion: 'Discuss both these views and give your own opinion.',
  problem_solution:
    'What problems does this cause and what solutions can you suggest?',
  advantages_disadvantages: 'Discuss the advantages and disadvantages.',
  double_question:
    'What are the reasons for this? What can be done to address it?',
}

export function getDefaultInstruction(
  taskNumber: number,
  essayType?: string | null,
): string {
  if (taskNumber === 1) return TASK1_DEFAULT_INSTRUCTION
  return (
    TASK2_DEFAULT_INSTRUCTIONS[essayType ?? '__default__'] ??
    TASK2_DEFAULT_INSTRUCTIONS.__default__
  )
}

export function getDefaultQuestion(
  essayType?: string | null,
): string | null {
  if (!essayType) return null
  return TASK2_QUESTION_PRESETS[essayType] ?? null
}
