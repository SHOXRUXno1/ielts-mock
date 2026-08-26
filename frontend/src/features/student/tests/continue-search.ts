import type { SectionType } from '@/features/tests/data/schema'
import { isSectionType } from '@/features/tests/lib/part-resolver'

export function continueTakeSearch(
  attemptId: string,
  section: string | null | undefined,
) {
  const skill: SectionType =
    section && isSectionType(section) ? section : 'listening'
  return {
    resume: attemptId,
    section: skill,
    part: skill === 'speaking' ? undefined : '1',
  }
}
