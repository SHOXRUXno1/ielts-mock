import { describe, expect, it } from 'vitest'
import {
  formatPassageParagraphLabel,
  hasTfngKeyLegend,
  hasYnngKeyLegend,
  splitPassageParagraphs,
} from './instruction-block'

describe('hasTfngKeyLegend', () => {
  it('detects the official TRUE/FALSE/NG key already in the instruction', () => {
    expect(
      hasTfngKeyLegend(
        'TRUE if the statement agrees with the information\nFALSE if the statement contradicts the information',
      ),
    ).toBe(true)
  })

  it('is false when the group only has a short lead-in', () => {
    expect(
      hasTfngKeyLegend(
        'Do the following statements agree with the information given in Reading Passage?',
      ),
    ).toBe(false)
  })
})

describe('hasYnngKeyLegend', () => {
  it('detects the official YES/NO/NG key already in the instruction', () => {
    expect(
      hasYnngKeyLegend('YES if the statement agrees with the claims of the writer'),
    ).toBe(true)
  })
})

describe('splitPassageParagraphs', () => {
  it('splits on a single newline (seeded Cambridge copy)', () => {
    expect(
      splitPassageParagraphs('First paragraph.\nSecond paragraph.\nThird.'),
    ).toEqual(['First paragraph.', 'Second paragraph.', 'Third.'])
  })

  it('splits on blank lines the same way', () => {
    expect(splitPassageParagraphs('Alpha.\n\nBeta.\n\n\nGamma.')).toEqual([
      'Alpha.',
      'Beta.',
      'Gamma.',
    ])
  })

  it('normalises Windows line endings and trims empty pieces', () => {
    expect(splitPassageParagraphs('One.\r\n\r\nTwo.\r\n')).toEqual([
      'One.',
      'Two.',
    ])
  })
})

describe('formatPassageParagraphLabel', () => {
  it('strips brackets from a single-letter paragraph label', () => {
    expect(formatPassageParagraphLabel('[A]')).toBe('A')
    expect(formatPassageParagraphLabel('[J]')).toBe('J')
  })

  it('leaves normal paragraphs unchanged', () => {
    expect(formatPassageParagraphLabel('Some body text.')).toBe('Some body text.')
    expect(formatPassageParagraphLabel('[A] extra')).toBe('[A] extra')
  })
})
