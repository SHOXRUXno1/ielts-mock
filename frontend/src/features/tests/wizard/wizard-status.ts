import { countScoringSlots, type Question, type Section, type Test } from '../data/schema'
import { countAuthoredSpeakingParts, questionsForSection } from '../lib/speaking-content'
import type { StepStatus } from './progress-bar'

export function computeWizardStatuses(
  test: Test | null,
  sections: Section[],
  questionsMap: Record<string, Question[]>,
): StepStatus[] {
  const infoStatus: StepStatus = test ? 'complete' : 'empty'

  function sectionStatus(type: string, expectedParts: number, expectedQPerPart?: number): StepStatus {
    if (!test) return 'locked'
    const ofType = sections.filter((s) => s.type === type)
    if (ofType.length === 0) return 'empty'
    const totalQ = ofType.reduce((acc, s) => {
      const qs = questionsForSection(s, questionsMap)
      if (qs.length > 0) return acc + countScoringSlots(qs)
      return acc + (s.question_count ?? 0)
    }, 0)
    if (ofType.length < expectedParts) return 'partial'
    if (totalQ === 0) return 'partial'
    if (expectedQPerPart && totalQ < expectedParts * expectedQPerPart) return 'partial'
    return 'complete'
  }

  const listeningStatus = sectionStatus('listening', 4, 10)
  const readingStatus = sectionStatus('reading', 3)

  const writingStatus: StepStatus = (() => {
    if (!test) return 'locked'
    const ws = sections.find((s) => s.type === 'writing')
    if (!ws) return 'empty'
    const qs = questionsForSection(ws, questionsMap)
    if (qs.length >= 2) return 'complete'
    if (qs.length === 1) return 'partial'
    return 'empty'
  })()

  const speakingStatus: StepStatus = (() => {
    if (!test) return 'locked'
    const sp = sections.filter((s) => s.type === 'speaking')
    if (sp.length === 0) return 'empty'
    const authored = countAuthoredSpeakingParts(sp, questionsMap)
    if (authored === 0) return 'empty'
    if (authored < 3 || sp.length < 3) return 'partial'
    return 'complete'
  })()

  const sectionStatuses = [listeningStatus, readingStatus, writingStatus, speakingStatus]
  const reviewStatus: StepStatus = sectionStatuses.every((s) => s === 'complete')
    ? 'complete'
    : sectionStatuses.some((s) => s === 'partial' || s === 'complete')
      ? 'partial'
      : !test
        ? 'locked'
        : 'empty'

  return [infoStatus, listeningStatus, readingStatus, writingStatus, speakingStatus, reviewStatus]
}
