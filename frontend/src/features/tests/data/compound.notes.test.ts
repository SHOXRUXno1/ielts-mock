import { describe, expect, it } from 'vitest'
import { asCompoundStructure, extractGapIds } from './compound'

describe('asCompoundStructure notes bullets', () => {
  it('preserves bullets: false', () => {
    const result = asCompoundStructure({
      variant: 'notes',
      title: 'Enquiry',
      bullets: false,
      instruction_words: 'ONE WORD ONLY',
      max_words_per_gap: 1,
      sections: [
        {
          heading: '',
          items: [{ segments: [{ type: 'text', value: 'Age: 18' }] }],
        },
      ],
    })
    expect(result).not.toBeNull()
    expect(result?.variant).toBe('notes')
    if (result?.variant === 'notes') {
      expect(result.bullets).toBe(false)
    }
  })

  it('defaults missing bullets to true for legacy notes', () => {
    const result = asCompoundStructure({
      variant: 'notes',
      title: 'Farm Tours',
      instruction_words: 'ONE WORD ONLY',
      max_words_per_gap: 1,
      sections: [
        {
          heading: '',
          items: [{ segments: [{ type: 'gap', gap_id: 'g1' }] }],
        },
      ],
    })
    expect(result).not.toBeNull()
    if (result?.variant === 'notes') {
      expect(result.bullets).toBe(true)
    }
  })
})

describe('extractGapIds', () => {
  it('counts a repeated gap_id once (7 ______ and ______)', () => {
    expect(
      extractGapIds({
        variant: 'table',
        instruction_words: 'NO MORE THAN TWO WORDS',
        max_words_per_gap: 2,
        headers: ['Part of tree', 'Traditional use'],
        rows: [
          [
            {
              variant: 'plain',
              segments: [
                { type: 'gap', gap_id: 'g7' },
                { type: 'text', value: ' and ' },
                { type: 'gap', gap_id: 'g7' },
              ],
            },
            { variant: 'plain', segments: [{ type: 'text', value: 'medicine' }] },
          ],
        ],
      }),
    ).toEqual(['g7'])
  })
})
