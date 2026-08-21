import { describe, expect, it } from 'vitest'
import {
  joinGapAnswerParts,
  splitJoinedGapAnswer,
} from './joined-gap-answer'

describe('splitJoinedGapAnswer', () => {
  it('splits an official "leaves and bark" key across two blanks', () => {
    expect(splitJoinedGapAnswer('leaves and bark', 2)).toEqual([
      'leaves',
      'bark',
    ])
  })

  it('splits a space-only key the same way', () => {
    expect(splitJoinedGapAnswer('leaves bark', 2)).toEqual(['leaves', 'bark'])
  })

  it('keeps a single stored answer in one blank', () => {
    expect(splitJoinedGapAnswer('branches', 1)).toEqual(['branches'])
  })
})

describe('joinGapAnswerParts', () => {
  it('joins two blanks with and', () => {
    expect(joinGapAnswerParts(['leaves', 'bark'])).toBe('leaves and bark')
  })

  it('does not invent and when only one blank is filled', () => {
    expect(joinGapAnswerParts(['leaves', ''])).toBe('leaves')
  })
})
