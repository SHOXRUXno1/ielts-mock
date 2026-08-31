import { describe, expect, it } from 'vitest'
import {
  adaptInstructionForScreen,
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

describe('adaptInstructionForScreen', () => {
  it('rewords matching information letter instructions for dropdowns', () => {
    expect(
      adaptInstructionForScreen(
        'Reading Passage 3 has ten paragraphs labelled A-J.\n'
          + 'Which paragraph contains the following information?\n'
          + 'Write the correct letter A-J in boxes 27-32 on your answer sheet.',
        'matching_information',
      ),
    ).toBe(
      'Reading Passage 3 has ten paragraphs labelled A-J.\n'
        + 'Which paragraph contains the following information?\n'
        + 'Select the correct letter, A–J, for each question.',
    )
  })

  it('rewords word-bank compound instructions and drops duplicate screen hints', () => {
    expect(
      adaptInstructionForScreen(
        'Complete the notes below using the list of words A-K from the box below.\n'
          + 'Write the correct letters in boxes 19-25 on your answer sheet.\n'
          + 'On screen, select the correct letter from the list for each gap.',
        'compound',
        { hasWordBank: true },
      ),
    ).toBe(
      'Complete the notes below using the list of words A-K from the box below.\n'
        + 'Select the correct letter from the list for each gap.',
    )
  })

  it('drops the paper-only TFNG lead-in when the key legend follows', () => {
    expect(
      adaptInstructionForScreen(
        'Do the following statements agree with the information given in Reading Passage 2?\n'
          + 'In boxes 14-18 on your answer sheet write\n'
          + 'TRUE if the statement agrees with the information\n'
          + 'FALSE if the statement contradicts the information\n'
          + 'NOT GIVEN if there is no information on this',
        'true_false_ng',
      ),
    ).toBe(
      'Do the following statements agree with the information given in Reading Passage 2?\n'
        + 'TRUE if the statement agrees with the information\n'
        + 'FALSE if the statement contradicts the information\n'
        + 'NOT GIVEN if there is no information on this',
    )
  })

  it('leaves free-text completion instructions unchanged', () => {
    const instruction =
      'Label the diagram below.\n'
      + 'Choose NO MORE THAN ONE WORD AND/OR A NUMBER from the passage for each answer.\n'
      + 'Write your answers in boxes 33-35 on your answer sheet.'
    expect(adaptInstructionForScreen(instruction, 'compound')).toBe(instruction)
  })
})
