import { describe, expect, it } from 'vitest'
import type { ExaminerScore } from '@/lib/api/speaking-examiner'
import { resolveScoreDialogHistory } from './resolve-score-dialog-history'

function baseScore(overrides: Partial<ExaminerScore> = {}): ExaminerScore {
  return {
    fluency_coherence: { band: 6, feedback: 'ok' },
    lexical_resource: { band: 6, feedback: 'ok' },
    grammatical_range: { band: 6, feedback: 'ok' },
    pronunciation: { band: 6, feedback: 'ok' },
    overall_band: 6,
    strengths: [],
    improvements: [],
    transcript: 'candidate only line',
    ...overrides,
  }
}

describe('resolveScoreDialogHistory', () => {
  it('prefers non-empty client history', () => {
    const client = [{ role: 'examiner' as const, text: 'Hello' }]
    const score = baseScore({
      conversation_history: [{ role: 'candidate', text: 'ignored' }],
    })

    expect(resolveScoreDialogHistory(score, client)).toEqual(client)
  })

  it('falls back to score.conversation_history when client history is empty', () => {
    const serverHistory = [
      { role: 'examiner' as const, text: 'Question one' },
      { role: 'candidate' as const, text: 'Answer one' },
    ]
    const score = baseScore({ conversation_history: serverHistory })

    expect(resolveScoreDialogHistory(score, [])).toEqual(serverHistory)
    expect(resolveScoreDialogHistory(score)).toEqual(serverHistory)
  })

  it('falls back to transcript candidate lines when no dialog history', () => {
    const score = baseScore({ transcript: 'line one\n\nline two' })

    expect(resolveScoreDialogHistory(score, [])).toEqual([
      { role: 'candidate', text: 'line one' },
      { role: 'candidate', text: 'line two' },
    ])
  })

  it('returns empty array for no-speech transcript', () => {
    const score = baseScore({ transcript: '(No speech detected)' })

    expect(resolveScoreDialogHistory(score, [])).toEqual([])
  })
})
