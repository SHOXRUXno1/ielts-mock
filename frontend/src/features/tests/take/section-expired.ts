import type { SectionType } from '../data/schema'
import { isSectionType } from '../lib/part-resolver'

export type SectionExpiredDetail = {
  code: 'SECTION_EXPIRED'
  message: string
  sealed_at: string | null
  next_section: string | null
}

export type SectionExpiredInfo = {
  from: SectionType | null
  next: SectionType | null
  message: string
  sealedAt: string | null
}

/** Extract structured SECTION_EXPIRED payload from an Axios-like error. */
export function parseSectionExpired(err: unknown): SectionExpiredDetail | null {
  const detail = (
    err as { response?: { status?: number; data?: { detail?: unknown } } }
  )?.response?.data?.detail
  if (!detail || typeof detail !== 'object') return null
  const d = detail as Record<string, unknown>
  if (d.code !== 'SECTION_EXPIRED') return null
  return {
    code: 'SECTION_EXPIRED',
    message: typeof d.message === 'string' ? d.message : 'Section time expired',
    sealed_at: typeof d.sealed_at === 'string' ? d.sealed_at : null,
    next_section: typeof d.next_section === 'string' ? d.next_section : null,
  }
}

export function toExpiredInfo(
  detail: SectionExpiredDetail,
  fallbackFrom: SectionType | null = null,
): SectionExpiredInfo {
  const nextRaw = detail.next_section
  return {
    from: fallbackFrom,
    next: nextRaw && isSectionType(nextRaw) ? nextRaw : null,
    message: detail.message,
    sealedAt: detail.sealed_at,
  }
}

/** True when an Axios error is a structured SECTION_EXPIRED 409. */
export function isSectionExpiredError(err: unknown): boolean {
  return parseSectionExpired(err) != null
}
