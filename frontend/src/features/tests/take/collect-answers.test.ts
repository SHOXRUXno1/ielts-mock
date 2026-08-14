import { describe, expect, it } from 'vitest'
import {
  collectAnswers,
  collectAnswersForTypes,
  sectionIdsForTypes,
} from './collect-answers'
import type { Section } from '../data/schema'

const sections = [
  { id: 'sec-l', type: 'listening', order: 1 },
  { id: 'sec-r', type: 'reading', order: 2 },
] as Section[]

describe('collectAnswers', () => {
  it('filters to active section only', () => {
    const answers = {
      'sec-l': { q1: { answer: 'a' } },
      'sec-r': { q2: { answer: 'b' } },
    }
    const ids = sectionIdsForTypes(sections, ['reading'])
    const payload = collectAnswers(answers, ids)
    expect(payload).toEqual([{ question_id: 'q2', response: { answer: 'b' } }])
  })

  it('collectAnswersForTypes skips sealed listening when saving reading', () => {
    const answers = {
      'sec-l': { q1: { answer: 'old' } },
      'sec-r': { q2: { answer: 'new' } },
    }
    expect(
      collectAnswersForTypes(answers, sections, ['reading']),
    ).toHaveLength(1)
  })
})
