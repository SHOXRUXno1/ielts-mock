import { describe, expect, it } from 'vitest'
import { assignGroupsSlotNumbers, type SlotNumberingGroup } from './schema'

describe('assignGroupsSlotNumbers', () => {
  it('numbers across groups when each group reuses local order 1..n', () => {
    const groups: SlotNumberingGroup[] = [
      {
        id: 'g1',
        order: 1,
        question_type: 'matching_information',
        questions: [1, 2, 3, 4, 5].map((order) => ({
          id: `g1q${order}`,
          order,
          question_type: 'matching_information',
          content: {},
          answer_key: { correct: 'A' },
        })),
      },
      {
        id: 'g2',
        order: 2,
        question_type: 'matching_features',
        questions: [1, 2, 3, 4, 5].map((order) => ({
          id: `g2q${order}`,
          order,
          question_type: 'matching_features',
          content: {},
          answer_key: { correct: 'A' },
        })),
      },
      {
        id: 'g3',
        order: 3,
        question_type: 'summary_completion',
        questions: [1, 2, 3].map((order) => ({
          id: `g3q${order}`,
          order,
          question_type: 'summary_completion',
          content: {},
          answer_key: { correct: 'word' },
        })),
      },
    ]

    const ranges = assignGroupsSlotNumbers(groups, 13) // Passage 2 → Q14+

    expect(ranges.get('g1q1')).toEqual({ start: 14, end: 14 })
    expect(ranges.get('g1q5')).toEqual({ start: 18, end: 18 })
    expect(ranges.get('g2q1')).toEqual({ start: 19, end: 19 })
    expect(ranges.get('g2q5')).toEqual({ start: 23, end: 23 })
    expect(ranges.get('g3q1')).toEqual({ start: 24, end: 24 })
    expect(ranges.get('g3q3')).toEqual({ start: 26, end: 26 })
  })

  it('multi_select spans choose_n slots before the next group', () => {
    const groups: SlotNumberingGroup[] = [
      {
        id: 'g1',
        order: 1,
        question_type: 'multi_select',
        questions: [
          {
            id: 'ms1',
            order: 1,
            question_type: 'multi_select',
            content: { choose_n: 2 },
            answer_key: { correct: ['A', 'B'] },
          },
        ],
      },
      {
        id: 'g2',
        order: 2,
        question_type: 'mcq',
        questions: [
          {
            id: 'mcq1',
            order: 1,
            question_type: 'mcq',
            content: {},
            answer_key: { correct: 'A' },
          },
        ],
      },
    ]

    const ranges = assignGroupsSlotNumbers(groups, 0)
    expect(ranges.get('ms1')).toEqual({ start: 1, end: 2 })
    expect(ranges.get('mcq1')).toEqual({ start: 3, end: 3 })
  })
})
