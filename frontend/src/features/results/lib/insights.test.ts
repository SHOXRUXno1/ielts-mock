import { describe, expect, it } from 'vitest'
import type { AnswerRead, AttemptDetailRead } from '@/lib/api/attempts'
import {
  accuracyByPart,
  formatRoundingExample,
  profileInsights,
  scoredSkills,
} from './insights'

function attempt(partial: Partial<AttemptDetailRead>): AttemptDetailRead {
  return {
    id: 'attempt-1',
    test_id: 'test-1',
    status: 'fully_scored',
    mode: 'full_mock',
    practice_section_id: null,
    practice_part_number: null,
    practice_section_type: null,
    practice_correct: null,
    practice_total: null,
    started_at: '2026-08-19T07:00:00.000Z',
    finished_at: '2026-08-19T10:00:00.000Z',
    overall_band: 7,
    listening_band: 7.5,
    reading_band: 7,
    writing_band: 6.5,
    speaking_band: 6,
    listening_raw: 32,
    reading_raw: 30,
    flagged_overtime: false,
    created_at: '2026-08-19T07:00:00.000Z',
    updated_at: '2026-08-19T10:00:00.000Z',
    answers: [],
    evaluation_jobs: [],
    speaking_session: null,
    test_title: 'Cambridge IELTS 15 – Test 1',
    ...partial,
  }
}

function answer(
  partial: Partial<AnswerRead> & { response: Record<string, unknown> },
): AnswerRead {
  return {
    id: 'a1',
    question_id: 'q1',
    is_correct: true,
    score: 1,
    question: null,
    section: { id: 's1', type: 'listening', order: 1 },
    ...partial,
  }
}

describe('profileInsights', () => {
  it('picks strongest, weakest, spread, and evenness', () => {
    const insights = profileInsights(attempt({}))
    expect(insights.strongest).toEqual({ key: 'listening', band: 7.5 })
    expect(insights.weakest).toEqual({ key: 'speaking', band: 6 })
    expect(insights.spread).toBe(1.5)
    expect(insights.even).toBe(false)
    expect(scoredSkills(attempt({})).map((row) => row.key)).toEqual([
      'listening',
      'reading',
      'writing',
      'speaking',
    ])
  })

  it('rounds a raw average to the nearest half band', () => {
    const insights = profileInsights(
      attempt({
        listening_band: 7,
        reading_band: 7,
        writing_band: 6.5,
        speaking_band: 6.5,
      }),
    )
    expect(insights.rawAverage).toBe(6.75)
    expect(insights.roundedAverage).toBe(7)
    expect(formatRoundingExample(insights)).toBe('6.8 → 7.0')
  })

  it('hides weakest and spread when only one skill is scored', () => {
    const insights = profileInsights(
      attempt({
        listening_band: 8,
        reading_band: null,
        writing_band: null,
        speaking_band: null,
        overall_band: null,
      }),
    )
    expect(insights.strongest).toEqual({ key: 'listening', band: 8 })
    expect(insights.weakest).toBeNull()
    expect(insights.spread).toBeNull()
    expect(insights.even).toBeNull()
    expect(insights.rawAverage).toBe(2)
    expect(insights.roundedAverage).toBe(2)
  })

  it('counts a skipped skill as 0 in the four-skill overall', () => {
    const insights = profileInsights(
      attempt({
        listening_band: 5,
        reading_band: 5,
        writing_band: 5,
        speaking_band: null,
        overall_band: 4,
      }),
    )
    expect(insights.rawAverage).toBe(3.75)
    expect(insights.roundedAverage).toBe(4)
    expect(formatRoundingExample(insights)).toBe('3.8 → 4.0')
  })
})

describe('accuracyByPart', () => {
  it('aggregates listening answers by part', () => {
    const rows = [
      answer({
        id: 'a1',
        is_correct: true,
        response: { answer: 'A' },
        section: { id: 's1', type: 'listening', order: 1 },
      }),
      answer({
        id: 'a2',
        is_correct: false,
        response: { answer: 'B' },
        section: { id: 's1', type: 'listening', order: 1 },
      }),
      answer({
        id: 'a3',
        is_correct: false,
        response: {},
        section: { id: 's2', type: 'listening', order: 2 },
      }),
    ]
    expect(accuracyByPart(null as unknown as AnswerRead[], 'listening')).toEqual([])
    const parts = accuracyByPart(rows, 'listening')
    expect(parts).toEqual([
      {
        key: 's1',
        label: 'Part 1',
        correct: 1,
        incorrect: 1,
        skipped: 0,
        total: 2,
      },
      {
        key: 's2',
        label: 'Part 2',
        correct: 0,
        incorrect: 0,
        skipped: 1,
        total: 1,
      },
    ])
  })
})
