import { describe, expect, it } from 'vitest'
import {
  correctChoiceKeys,
  isChoiceReview,
  matchingPairs,
  normalizeChoice,
  questionStem,
  reviewOptions,
  studentChoiceKeys,
} from './review'

describe('questionStem', () => {
  it('prefers statement for True/False/NG', () => {
    expect(
      questionStem({ statement: 'Hotels are cheap.', question: 'ignore' }, 'true_false_ng'),
    ).toBe('Hotels are cheap.')
  })

  it('falls back across common content keys', () => {
    expect(questionStem({ prompt: 'The meeting is on ______' }, 'short_answer')).toBe(
      'The meeting is on ______',
    )
  })
})

describe('reviewOptions', () => {
  it('builds lettered MCQ options', () => {
    expect(reviewOptions({ options: ['River Inn', 'Park Hotel'] }, 'mcq')).toEqual([
      { letter: 'A', label: 'River Inn' },
      { letter: 'B', label: 'Park Hotel' },
    ])
  })

  it('keeps True / False / Not Given labels', () => {
    expect(reviewOptions({}, 'true_false_ng').map((o) => o.letter)).toEqual([
      'True',
      'False',
      'Not Given',
    ])
  })

  it('parses already-prefixed options', () => {
    expect(reviewOptions({ options: ['A. a hotel', 'B a cafe'] }, 'matching_features')).toEqual([
      { letter: 'A', label: 'a hotel' },
      { letter: 'B', label: 'a cafe' },
    ])
  })
})

describe('choice keys', () => {
  const options = reviewOptions({ options: ['River Inn', 'Park Hotel'] }, 'mcq')

  it('normalizes a full-text pick to a letter', () => {
    expect(normalizeChoice('Park Hotel', options)).toBe('B')
    expect(normalizeChoice('a', options)).toBe('A')
  })

  it('reads student and correct letters', () => {
    expect(studentChoiceKeys({ answer: 'River Inn' }, options)).toEqual(['A'])
    expect(correctChoiceKeys({ correct: ['B', 'A'] }, options)).toEqual(['B', 'A'])
  })

  it('treats MCQ with options as a choice review', () => {
    expect(isChoiceReview('mcq', options)).toBe(true)
    expect(isChoiceReview('matching', options)).toBe(false)
  })
})

describe('matchingPairs', () => {
  it('pairs left items with student and correct maps', () => {
    expect(
      matchingPairs(
        { left: ['Hotel', 'Park'] },
        { answer: { Hotel: 'A', Park: 'C' } },
        { correct: { Hotel: 'B', Park: 'C' } },
      ),
    ).toEqual([
      { item: 'Hotel', student: 'A', correct: 'B' },
      { item: 'Park', student: 'C', correct: 'C' },
    ])
  })
})
