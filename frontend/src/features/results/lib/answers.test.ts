import { describe, expect, it } from 'vitest'
import type { AnswerRead, QuestionSnapshot } from '@/lib/api/attempts'
import {
  answerMarks,
  answerOutcome,
  formatCorrectAnswer,
  formatStudentAnswer,
  groupAnswersByPart,
  splitChoiceLetters,
  tallyMarks,
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

/** "Choose TWO letters" — one question row spanning two question numbers. */
function chooseTwo(correct: string[]): QuestionSnapshot {
  return {
    id: 'q1',
    section_id: 's1',
    order: 1,
    question_type: 'multi_select',
    content: { choose_n: 2, options: ['a', 'b', 'c', 'd', 'e'] },
    answer_key: { correct },
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

describe('splitChoiceLetters', () => {
  it('reads a single option letter', () => {
    expect(splitChoiceLetters('B')).toEqual(['B'])
    expect(splitChoiceLetters('d')).toEqual(['D'])
  })

  it('reads joined option letters', () => {
    expect(splitChoiceLetters('B, D')).toEqual(['B', 'D'])
    expect(splitChoiceLetters('A | C')).toEqual(['A', 'C'])
  })

  it('leaves ordinary text alone', () => {
    expect(splitChoiceLetters('river')).toBeNull()
    expect(splitChoiceLetters('NOT GIVEN')).toBeNull()
    expect(splitChoiceLetters('TRUE')).toBeNull()
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

  it('marks one of two letters right as partial, not incorrect', () => {
    expect(
      answerOutcome(
        answer({
          response: { answer: ['D', 'C'] },
          is_correct: false,
          score: 0.5,
          question: chooseTwo(['B', 'C']),
        }),
      ),
    ).toBe('partial')
  })
})

describe('answerMarks', () => {
  it('gives one of the two marks when one letter matches', () => {
    expect(
      answerMarks(
        answer({
          response: { answer: ['D', 'C'] },
          is_correct: false,
          score: 0.5,
          question: chooseTwo(['B', 'C']),
        }),
      ),
    ).toEqual({ earned: 1, total: 2 })
  })

  it('gives both marks when the pair is fully right', () => {
    expect(
      answerMarks(
        answer({
          response: { answer: ['B', 'D'] },
          is_correct: true,
          score: 1,
          question: chooseTwo(['B', 'D']),
        }),
      ),
    ).toEqual({ earned: 2, total: 2 })
  })

  it('gives neither mark when no letter matches', () => {
    expect(
      answerMarks(
        answer({
          response: { answer: ['A', 'E'] },
          is_correct: false,
          score: 0,
          question: chooseTwo(['B', 'C']),
        }),
      ),
    ).toEqual({ earned: 0, total: 2 })
  })

  it('never awards a full pair to an answer the server called wrong', () => {
    expect(
      answerMarks(
        answer({
          response: { answer: ['B', 'C'] },
          is_correct: false,
          score: 0.9,
          question: chooseTwo(['B', 'C']),
        }),
      ),
    ).toEqual({ earned: 1, total: 2 })
  })

  it('keeps single-mark questions whole', () => {
    expect(
      answerMarks(answer({ response: { answer: 'river' }, is_correct: true, score: 1 })),
    ).toEqual({ earned: 1, total: 1 })
    expect(
      answerMarks(answer({ response: { answer: 'lake' }, is_correct: false, score: 0 })),
    ).toEqual({ earned: 0, total: 1 })
  })
})

describe('tallyMarks', () => {
  it('counts marks rather than rows, so a half-right pair splits', () => {
    const rows = [
      answer({ id: 'a1', response: { answer: 'river' }, is_correct: true, score: 1 }),
      answer({
        id: 'a2',
        response: { answer: ['D', 'C'] },
        is_correct: false,
        score: 0.5,
        question: chooseTwo(['B', 'C']),
      }),
      answer({ id: 'a3', response: {}, is_correct: false, score: 0 }),
    ]
    expect(tallyMarks(rows)).toEqual({ correct: 2, incorrect: 1, skipped: 1 })
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
