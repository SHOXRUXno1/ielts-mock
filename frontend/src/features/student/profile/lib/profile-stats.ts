import type { PracticeResultRow } from '@/lib/api/practice'
import type { SectionBands, StudentResult } from '@/lib/api/student'
import { SKILL_KEYS, type SkillKey } from '@/features/results/lib/skill'
import { formatAttemptDate } from '@/features/results/lib/status'

export type LoginKind = 'phone' | 'handle'

export type SkillHighlights = {
  strongest: SkillKey | null
  weakest: SkillKey | null
}

export type LifetimeStats = {
  mockTests: number
  practiceSessions: number
  activeSince: string | null
}

const PHONE_LOGIN = /^\+?\d{7,15}$/

export function loginKind(login: string): LoginKind {
  const compact = login.replace(/[\s\-().]/g, '')
  return PHONE_LOGIN.test(compact) ? 'phone' : 'handle'
}

export function skillHighlights(bands: SectionBands): SkillHighlights {
  const scored = SKILL_KEYS.flatMap((key) => {
    const band = bands[key]
    return band == null ? [] : [{ key, band }]
  })

  if (scored.length === 0) {
    return { strongest: null, weakest: null }
  }

  let strongest = scored[0]
  let weakest = scored[0]
  for (const item of scored) {
    if (item.band > strongest.band) strongest = item
    if (item.band < weakest.band) weakest = item
  }

  return { strongest: strongest.key, weakest: weakest.key }
}

function earliestIso(dates: Array<string | null | undefined>): string | null {
  let earliest: string | null = null
  let earliestMs = Number.POSITIVE_INFINITY

  for (const date of dates) {
    if (!date) continue
    const ms = new Date(date).getTime()
    if (!Number.isFinite(ms) || ms >= earliestMs) continue
    earliestMs = ms
    earliest = date
  }

  return earliest
}

export function lifetimeStats(
  results: StudentResult[] | null | undefined,
  practice: PracticeResultRow[] | null | undefined,
): LifetimeStats {
  const mock = Array.isArray(results) ? results : []
  const sessions = Array.isArray(practice) ? practice : []

  return {
    mockTests: mock.length,
    practiceSessions: sessions.length,
    activeSince: earliestIso([
      ...mock.map((row) => row.started_at ?? row.created_at),
      ...sessions.map((row) => row.started_at ?? row.created_at),
    ]),
  }
}

export function sessionExpiry(exp: number | null | undefined): string {
  if (exp == null || !Number.isFinite(exp) || exp <= 0) return '—'
  return formatAttemptDate(new Date(exp * 1000).toISOString())
}
