import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import type { WritingFeedbackRequest, WritingFeedbackResult } from './feedback'

// ── countWords (mirrored logic from writing-section) ─────────────────────────

function countWords(text: string): number {
  return text
    .trim()
    .split(/\s+/)
    .filter((w) => w.length > 0).length
}

describe('countWords', () => {
  it('returns 0 for empty string', () => {
    expect(countWords('')).toBe(0)
    expect(countWords('   ')).toBe(0)
  })

  it('counts simple words', () => {
    expect(countWords('hello world')).toBe(2)
    expect(countWords('one two three four five')).toBe(5)
  })

  it('handles multiple spaces and newlines', () => {
    expect(countWords('hello   world\n\ntest')).toBe(3)
  })

  it('counts a typical 150-word passage', () => {
    const text = Array.from({ length: 150 }, (_, i) => `word${i}`).join(' ')
    expect(countWords(text)).toBe(150)
  })
})

// ── DRAFT_KEY helper ─────────────────────────────────────────────────────────

function draftKey(attemptId: string, questionId: string): string {
  return `writing:${attemptId}:${questionId}`
}

describe('draftKey', () => {
  it('builds consistent localStorage key', () => {
    expect(draftKey('attempt-123', 'question-456')).toBe(
      'writing:attempt-123:question-456',
    )
  })

  it('produces unique keys per question', () => {
    const k1 = draftKey('a1', 'q1')
    const k2 = draftKey('a1', 'q2')
    expect(k1).not.toBe(k2)
  })
})

// ── WritingFeedbackResult type shape ─────────────────────────────────────────

describe('WritingFeedbackResult shape', () => {
  const sample: WritingFeedbackResult = {
    overall_band: 6.5,
    task_achievement: { band: 7.0, feedback: 'Well addressed.' },
    coherence_cohesion: { band: 6.0, feedback: 'Organised.' },
    lexical_resource: { band: 6.5, feedback: 'Adequate range.' },
    grammatical_range: { band: 6.5, feedback: 'Mixed structures.' },
    strengths: ['Clear overview'],
    improvements: ['Use more precise vocabulary'],
    errors: [
      {
        quote: 'informations',
        type: 'grammar',
        correction: 'information',
        explanation: "'information' is uncountable.",
      },
    ],
    word_count: 162,
  }

  it('overall_band is a number', () => {
    expect(typeof sample.overall_band).toBe('number')
    expect(sample.overall_band).toBe(6.5)
  })

  it('criteria have band and feedback', () => {
    expect(sample.task_achievement?.band).toBe(7.0)
    expect(typeof sample.task_achievement?.feedback).toBe('string')
  })

  it('errors array has required fields', () => {
    const err = sample.errors[0]
    expect(err).toHaveProperty('quote')
    expect(err).toHaveProperty('type')
    expect(err).toHaveProperty('correction')
    expect(err).toHaveProperty('explanation')
  })

  it('strengths and improvements are string arrays', () => {
    expect(Array.isArray(sample.strengths)).toBe(true)
    expect(Array.isArray(sample.improvements)).toBe(true)
    expect(typeof sample.strengths[0]).toBe('string')
  })
})

// ── requestWritingFeedback (mocked axios) ─────────────────────────────────────

describe('requestWritingFeedback', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('posts to /admin/feedback/writing and returns data', async () => {
    const mockResult: WritingFeedbackResult = {
      overall_band: 7.0,
      task_achievement: null,
      coherence_cohesion: null,
      lexical_resource: null,
      grammatical_range: null,
      strengths: [],
      improvements: [],
      errors: [],
      word_count: 200,
    }

    vi.doMock('@/lib/axios', () => ({
      api: {
        post: vi.fn().mockResolvedValue({ data: mockResult }),
      },
    }))

    const { requestWritingFeedback } = await import('./feedback')

    const payload: WritingFeedbackRequest = {
      task: 1,
      prompt: 'Describe the chart.',
      text: 'The chart illustrates employment trends.',
    }

    const result = await requestWritingFeedback(payload)
    expect(result.overall_band).toBe(7.0)
    expect(result.word_count).toBe(200)
  })
})
