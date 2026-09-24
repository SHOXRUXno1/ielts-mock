import { scoringSlotsForQuestion, type Question } from '../data/schema'
import type { SectionAnswers } from './take-test-context'

function hasResponseValue(response: Record<string, unknown>): boolean {
  return Object.values(response).some((value) => {
    if (value === '' || value === null || value === undefined) return false
    if (Array.isArray(value)) return value.length > 0
    if (typeof value === 'object') return Object.keys(value).length > 0
    return true
  })
}

/**
 * Number of IELTS scoring slots a student has answered in one section.
 *
 * The two multi-select renderers persist their selections under different
 * response keys (`selected` and `answer`), so both are intentionally handled.
 */
export function countAnsweredSlots(
  sectionAnswers: SectionAnswers,
  questions: Question[]
): number {
  const questionsById = new Map(
    questions.map((question) => [question.id, question])
  )
  let count = 0

  for (const [questionId, response] of Object.entries(sectionAnswers)) {
    if (!hasResponseValue(response)) continue

    const question = questionsById.get(questionId)
    const selected = Array.isArray(response.answer)
      ? response.answer
      : Array.isArray(response.selected)
        ? response.selected
        : null

    if (question?.question_type === 'multi_select' && selected) {
      count += Math.min(selected.length, scoringSlotsForQuestion(question))
    } else {
      count += 1
    }
  }

  return count
}
