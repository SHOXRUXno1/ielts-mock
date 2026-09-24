/**
 * An absent entry means the section request is still in flight. An empty
 * entry means it finished and the section genuinely contains no questions.
 */
export function hasLoadedQuestions(
  sectionQuestions: Record<string, unknown[]>,
  sectionId: string,
): boolean {
  return Object.prototype.hasOwnProperty.call(sectionQuestions, sectionId)
}
