import { describe, expect, it } from 'vitest'
import {
  asSectionType,
  isNextSection,
  nextTypeAfter,
  nextUnlockableType,
} from './section-order'
import type { SectionType } from '../data/schema'

const ORDER: SectionType[] = [
  'listening',
  'reading',
  'writing',
  'speaking',
]

describe('section-order', () => {
  it('nextTypeAfter returns the neighbour or null at the end', () => {
    expect(nextTypeAfter(ORDER, 'listening')).toBe('reading')
    expect(nextTypeAfter(ORDER, 'speaking')).toBeNull()
    expect(asSectionType('writing')).toBe('writing')
    expect(asSectionType('nope')).toBeNull()
  })

  it('isNextSection only allows immediate neighbour', () => {
    expect(isNextSection('listening', 'reading', ORDER)).toBe(true)
    expect(isNextSection('listening', 'writing', ORDER)).toBe(false)
    expect(isNextSection('reading', 'writing', ORDER)).toBe(true)
  })

  it('nextUnlockableType unlocks only the section after active', () => {
    const stateOf = (t: string) =>
      t === 'listening' ? 'active' : 'not_started'
    expect(nextUnlockableType(ORDER, stateOf, 'listening')).toBe('reading')
  })

  it('does not unlock writing while listening is active', () => {
    const stateOf = (t: string) =>
      t === 'listening' ? 'active' : 'not_started'
    expect(nextUnlockableType(ORDER, stateOf, 'listening')).not.toBe(
      'writing',
    )
  })
})
