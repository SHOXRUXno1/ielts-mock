import { describe, expect, it } from 'vitest'
import { asCompoundStructure } from './compound'

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
