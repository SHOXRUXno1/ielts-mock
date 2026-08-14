import { scoringSlotsForQuestion, type Question } from '../data/schema'

function isAnswered(
  response: Record<string, unknown> | undefined,
): boolean {
  if (!response) return false
  return Object.values(response).some((v) => {
    if (v === '' || v === null || v === undefined) return false
    if (Array.isArray(v)) return v.length > 0
    if (typeof v === 'object') return Object.keys(v as object).length > 0
    return true
  })
}

/** True if the student has given any scorable response for this question. */
export function isQuestionAnswered(
  question: Question,
  response: Record<string, unknown> | undefined,
): boolean {
  if (!response) return false
  const slots = scoringSlotsForQuestion(question)
  // multi_select: answered if any selection present (shared across slot cells)
  if (slots > 1) {
    const arr = Array.isArray(response.answer)
      ? response.answer
      : Array.isArray(response.selected)
        ? response.selected
        : null
    if (arr) return arr.length > 0
  }
  return isAnswered(response)
}

export type QuestionNavEntry = {
  question: Question
  sectionId: string
  displayNumber: number
}

/** Flatten a section's questions into one nav cell per IELTS display number. */
export function questionNavEntries(
  questions: Question[],
  sectionId: string,
): QuestionNavEntry[] {
  const qs = [...questions].sort((a, b) => {
    const aN = a.computed_number ?? a.order
    const bN = b.computed_number ?? b.order
    return aN - bN
  })
  const entries: QuestionNavEntry[] = []
  for (const q of qs) {
    const start = q.computed_number ?? q.order
    const end =
      typeof q.computed_number_end === 'number' ? q.computed_number_end : start
    for (let n = start; n <= end; n++) {
      entries.push({ question: q, sectionId, displayNumber: n })
    }
  }
  return entries
}
