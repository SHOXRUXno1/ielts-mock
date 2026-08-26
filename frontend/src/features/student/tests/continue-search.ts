import type { SectionType } from '@/features/tests/data/schema'
import { isSectionType } from '@/features/tests/lib/part-resolver'
import { lsKeyForAttempt } from '@/features/tests/take/constants'

export type LocalResume = {
  section?: string
  part?: string
}

function parsePart(value: unknown): number | null {
  const n = typeof value === 'number' ? value : parseInt(String(value ?? ''), 10)
  return Number.isFinite(n) && n >= 1 ? Math.floor(n) : null
}

export function readLocalResume(attemptId: string): LocalResume | null {
  if (typeof localStorage === 'undefined') return null
  try {
    const raw = localStorage.getItem(lsKeyForAttempt(attemptId))
    if (!raw) return null
    const saved = JSON.parse(raw) as { resume?: LocalResume }
    return saved.resume ?? null
  } catch {
    return null
  }
}

export function continueTakeSearch(
  attemptId: string,
  section: string | null | undefined,
  part?: number | string | null,
) {
  const skill: SectionType =
    section && isSectionType(section) ? section : 'listening'
  if (skill === 'speaking') {
    return { resume: attemptId, section: skill, part: undefined }
  }
  const local = readLocalResume(attemptId)
  const localPart = local?.section === skill ? parsePart(local.part) : null
  const resolved = localPart ?? parsePart(part) ?? 1
  return {
    resume: attemptId,
    section: skill,
    part: String(resolved),
  }
}
