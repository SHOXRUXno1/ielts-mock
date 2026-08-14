import type { Section, SectionType } from '../data/schema'
import type { SectionAnswers } from './take-test-context'

export type AnswerPayload = {
  question_id: string
  response: Record<string, unknown>
}

/** Collect non-empty answers, optionally limited to section row ids. */
export function collectAnswers(
  answers: Record<string, SectionAnswers>,
  sectionIds?: Set<string> | null,
): AnswerPayload[] {
  const all: AnswerPayload[] = []
  for (const [sectionId, sectionAnswers] of Object.entries(answers)) {
    if (sectionIds && !sectionIds.has(sectionId)) continue
    for (const [questionId, response] of Object.entries(sectionAnswers)) {
      if (Object.keys(response).length > 0) {
        all.push({ question_id: questionId, response })
      }
    }
  }
  return all
}

export function sectionIdsForTypes(
  sortedSections: Section[],
  types: Iterable<SectionType | string>,
): Set<string> {
  const want = new Set(types)
  const ids = new Set<string>()
  for (const s of sortedSections) {
    if (want.has(s.type)) ids.add(s.id)
  }
  return ids
}

/** Answers belonging to the given section type(s) only. */
export function collectAnswersForTypes(
  answers: Record<string, SectionAnswers>,
  sortedSections: Section[],
  types: Iterable<SectionType | string>,
): AnswerPayload[] {
  return collectAnswers(answers, sectionIdsForTypes(sortedSections, types))
}
