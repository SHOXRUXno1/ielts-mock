import { describe, expect, it } from 'vitest'
import type { Question } from '../data/schema'
import { countAnsweredSlots } from './answer-progress'
import type { SectionAnswers } from './take-test-context'

const multiSelect = {
  id: 'pair',
  question_type: 'multi_select',
  content: { choose_n: 2 },
} as Question

describe('countAnsweredSlots', () => {
  it.each([
    ['compound pair answer', { pair: { answer: ['B', 'C'] } }],
    ['standard selected answer', { pair: { selected: ['B', 'C'] } }],
  ])('counts each option in a %s', (_label, answers) => {
    expect(countAnsweredSlots(answers as SectionAnswers, [multiSelect])).toBe(2)
  })

  it('does not count empty responses', () => {
    expect(countAnsweredSlots({ pair: { answer: [] } }, [multiSelect])).toBe(0)
  })
})
