import { describe, expect, it } from 'vitest'
import { splitPassageParagraphs } from './instruction-block'

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
