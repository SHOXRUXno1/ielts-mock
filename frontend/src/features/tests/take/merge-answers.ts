import type { SectionAnswers } from './take-test-context'

/**
 * Merge localStorage answers with server answers.
 * Server wins on overlapping question ids; LS fills gaps only.
 */
export function mergeAnswersServerWins(
  local: Record<string, SectionAnswers>,
  server: Record<string, SectionAnswers>,
): Record<string, SectionAnswers> {
  const sectionIds = new Set([
    ...Object.keys(local),
    ...Object.keys(server),
  ])
  const merged: Record<string, SectionAnswers> = {}
  for (const sid of sectionIds) {
    merged[sid] = {
      ...(local[sid] ?? {}),
      ...(server[sid] ?? {}),
    }
  }
  return merged
}
