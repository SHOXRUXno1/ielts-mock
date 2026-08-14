/** FastAPI 409 details that mean the section state already moved on. */
const BENIGN_DETAILS = new Set([
  'Section not active',
  'Section already completed',
  'Section not started',
])

export function sectionConflictDetail(err: unknown): string | null {
  const detail = (err as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail
  return typeof detail === 'string' ? detail : null
}

export function isBenignSectionConflict(err: unknown): boolean {
  const detail = sectionConflictDetail(err)
  return detail != null && BENIGN_DETAILS.has(detail)
}
