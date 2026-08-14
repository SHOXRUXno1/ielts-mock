import { describe, expect, it } from 'vitest'
import type { SectionType } from '../data/schema'
import { TYPE_ORDER } from './constants'
import { resolveSealedRedirectTarget } from './section-guard-logic'

describe('sealed section redirect target', () => {
  it('redirects sealed listening to active reading', () => {
    const sealed = new Set<SectionType>(['listening'])
    expect(
      resolveSealedRedirectTarget({
        hold: false,
        sealedTypes: sealed,
        activeType: 'reading',
        presentTypes: [...TYPE_ORDER],
        current: 'listening',
      }),
    ).toBe('reading')
  })

  it('redirects to review when all sealed', () => {
    const sealed = new Set<SectionType>([
      'listening',
      'reading',
      'writing',
      'speaking',
    ])
    expect(
      resolveSealedRedirectTarget({
        hold: false,
        sealedTypes: sealed,
        activeType: null,
        presentTypes: [...TYPE_ORDER],
        current: 'listening',
      }),
    ).toBe('review')
  })

  it('falls back to first unsealed when no active', () => {
    const sealed = new Set<SectionType>(['listening'])
    expect(
      resolveSealedRedirectTarget({
        hold: false,
        sealedTypes: sealed,
        activeType: null,
        presentTypes: [...TYPE_ORDER],
        current: 'listening',
      }),
    ).toBe('reading')
  })

  it('does not redirect or enter while Time\'s up holds the handoff', () => {
    const sealed = new Set<SectionType>(['reading'])
    expect(
      resolveSealedRedirectTarget({
        hold: true,
        sealedTypes: sealed,
        activeType: null,
        presentTypes: [...TYPE_ORDER],
        current: 'reading',
      }),
    ).toBeNull()
  })
})
