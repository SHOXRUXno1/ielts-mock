import { describe, expect, it } from 'vitest'
import type { PracticeResultRow } from '@/lib/api/practice'
import type { StudentResult } from '@/lib/api/student'
import {
  lifetimeStats,
  loginKind,
  sessionExpiry,
  skillHighlights,
} from './profile-stats'

const emptyBands = {
  listening: null,
  reading: null,
  writing: null,
  speaking: null,
}

function result(createdAt: string, startedAt: string | null = null): StudentResult {
  return {
    id: createdAt,
    test_id: 't1',
    test_title: 'Test',
    status: 'fully_scored',
    overall_band: 6.5,
    listening_band: 7,
    reading_band: 6.5,
    writing_band: 6,
    speaking_band: 6.5,
    started_at: startedAt,
    finished_at: createdAt,
    created_at: createdAt,
  }
}

function practice(createdAt: string): PracticeResultRow {
  return {
    id: createdAt,
    test_id: 't1',
    test_title: 'Test',
    status: 'fully_scored',
    scope: 'part',
    section_type: 'listening',
    part_number: 1,
    correct: 8,
    total: 10,
    band: 7,
    started_at: null,
    finished_at: createdAt,
    created_at: createdAt,
  }
}

describe('loginKind', () => {
  it('recognizes phone logins', () => {
    expect(loginKind('+998912762770')).toBe('phone')
    expect(loginKind('998 91 276 27 70')).toBe('phone')
    expect(loginKind('(998) 912-762770')).toBe('phone')
  })

  it('treats names and emails as handles', () => {
    expect(loginKind('alibek')).toBe('handle')
    expect(loginKind('student@school.uz')).toBe('handle')
  })
})

describe('skillHighlights', () => {
  it('returns empty highlights when no skill is scored', () => {
    expect(skillHighlights(emptyBands)).toEqual({
      strongest: null,
      weakest: null,
    })
  })

  it('picks the highest and lowest scored skills', () => {
    expect(
      skillHighlights({
        listening: 8,
        reading: 6.5,
        writing: 5.5,
        speaking: 7,
      }),
    ).toEqual({ strongest: 'listening', weakest: 'writing' })
  })

  it('uses the same skill when only one band exists', () => {
    expect(
      skillHighlights({
        ...emptyBands,
        reading: 6,
      }),
    ).toEqual({ strongest: 'reading', weakest: 'reading' })
  })
})

describe('lifetimeStats', () => {
  it('returns zeros when there is no history', () => {
    expect(lifetimeStats([], [])).toEqual({
      mockTests: 0,
      practiceSessions: 0,
      activeSince: null,
    })
    expect(lifetimeStats(undefined, null)).toEqual({
      mockTests: 0,
      practiceSessions: 0,
      activeSince: null,
    })
  })

  it('counts attempts and finds the earliest date', () => {
    expect(
      lifetimeStats(
        [
          result('2026-03-01T00:00:00.000Z'),
          result('2026-04-01T00:00:00.000Z', '2026-01-15T00:00:00.000Z'),
        ],
        [practice('2026-02-01T00:00:00.000Z')],
      ),
    ).toEqual({
      mockTests: 2,
      practiceSessions: 1,
      activeSince: '2026-01-15T00:00:00.000Z',
    })
  })
})

describe('sessionExpiry', () => {
  it('returns an em dash when the token has no expiry', () => {
    expect(sessionExpiry(undefined)).toBe('—')
    expect(sessionExpiry(0)).toBe('—')
  })

  it('formats a unix expiry as a locale date', () => {
    const exp = Date.UTC(2026, 11, 31, 12, 0, 0) / 1000
    expect(sessionExpiry(exp)).toContain('2026')
  })
})
