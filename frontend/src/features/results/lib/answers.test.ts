import { describe, expect, it } from 'vitest'
import type { AnswerRead } from '@/lib/api/attempts'
import {
  answerOutcome,
  formatCorrectAnswer,
  formatStudentAnswer,
  groupAnswersByPart,
} from './answers'

function answer(partial: Partial<AnswerRead> & { response: Record<string, unknown> }): AnswerRead {
  return {
    id: 'a1',
    question_id: 'q1',
    is_correct: false,
    score: 0,
    question: null,
    section: null,
    ...partial,
  }
}

describe('formatStudentAnswer', () => {
  it('treats empty values as no answer', () => {
    expect(formatStudentAnswer({})).toBe('(no answer)')
    expect(formatStudentAnswer({ answer: '' })).toBe('(no answer)')
    expect(formatStudentAnswer({ answer: null })).toBe('(no answer)')
  })

  it('joins arrays and maps objects', () => {
    expect(formatStudentAnswer({ answer: ['B', 'D'] })).toBe('B, D')
    expect(formatStudentAnswer({ answer: { 1: 'A', 2: 'C' } })).toBe('1 → A; 2 → C')
  })
})

describe('formatCorrectAnswer', () => {
  it('prefers accepted_answers then correct/answer', () => {
    expect(formatCorrectAnswer({ accepted_answers: ['jamieson', 'Jamieson'] })).toBe(
      'jamieson | Jamieson',
    )
    expect(formatCorrectAnswer({ correct: ['B', 'A'] })).toBe('A | B')
    expect(formatCorrectAnswer({ answers: ['C'] })).toBe('C')
    expect(formatCorrectAnswer(null)).toBe('')
  })
})

describe('answerOutcome', () => {
  it('marks empty responses as skipped', () => {
    expect(answerOutcome(answer({ response: {}, is_correct: false }))).toBe('skipped')
  })

  it('marks is_correct true as correct', () => {
    expect(
      answerOutcome(answer({ response: { answer: 'river' }, is_correct: true })),
    ).toBe('correct')
  })

  it('marks a wrong filled answer as incorrect', () => {
    expect(
      answerOutcome(answer({ response: { answer: 'lake' }, is_correct: false })),
    ).toBe('incorrect')
  })
})

describe('groupAnswersByPart', () => {
  it('groups listening answers by section order', () => {
    const rows = [
      answer({
        id: 'a2',
        response: { answer: 'B' },
        section: { id: 's2', type: 'listening', order: 2 },
      }),
      answer({
        id: 'a1',
        response: { answer: 'A' },
        section: { id: 's1', type: 'listening', order: 1 },
      }),
    ]
    const groups = groupAnswersByPart(rows, 'listening')
    expect(groups.map((g) => g.label)).toEqual(['Part 1', 'Part 2'])
  })
})
