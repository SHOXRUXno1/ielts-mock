import type { Question } from '../data/schema'

/** DOM id for a display question number, e.g. q-23 */
export function questionAnchorId(displayNumber: number): string {
  return `q-${displayNumber}`
}

/** First display number for a question (computed_number or order). */
export function questionDisplayStart(question: Question): number {
  return question.computed_number ?? question.order
}

/** Inclusive end of display range for multi-slot questions. */
export function questionDisplayEnd(question: Question): number {
  if (typeof question.computed_number_end === 'number') {
    return question.computed_number_end
  }
  return questionDisplayStart(question)
}

/** All anchor ids for a question's display range. */
export function questionAnchorIds(question: Question): string[] {
  const start = questionDisplayStart(question)
  const end = questionDisplayEnd(question)
  const ids: string[] = []
  for (let n = start; n <= end; n++) {
    ids.push(questionAnchorId(n))
  }
  return ids
}
