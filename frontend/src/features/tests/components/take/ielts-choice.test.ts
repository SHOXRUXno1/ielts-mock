import { describe, expect, it } from 'vitest'
import {
  canonicalIeltsChoice,
  TRUE_FALSE_NG_CHOICES,
  YES_NO_NG_CHOICES,
} from './ielts-choice'

describe('IELTS three-choice answers', () => {
  it('stores the official uppercase values for True / False / Not Given', () => {
    expect(TRUE_FALSE_NG_CHOICES.map((choice) => choice.value)).toEqual([
      'TRUE',
      'FALSE',
      'NOT GIVEN',
    ])
  })

  it('stores the official uppercase values for Yes / No / Not Given', () => {
    expect(YES_NO_NG_CHOICES.map((choice) => choice.value)).toEqual([
      'YES',
      'NO',
      'NOT GIVEN',
    ])
  })

  it('keeps older title-cased saved answers selected', () => {
    expect(canonicalIeltsChoice('True')).toBe('TRUE')
    expect(canonicalIeltsChoice('Not Given')).toBe('NOT GIVEN')
  })
})
