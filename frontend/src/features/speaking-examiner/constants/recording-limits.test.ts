import { describe, expect, it } from 'vitest'
import {
  RECORDING_LIMITS,
  limitForTurn,
  resolveTurnKind,
} from './recording-limits'

describe('resolveTurnKind', () => {
  it('maps part 1 and part 3 regardless of the long-turn flag', () => {
    expect(resolveTurnKind(1, false)).toBe('part1')
    expect(resolveTurnKind(1, true)).toBe('part1')
    expect(resolveTurnKind(3, false)).toBe('part3')
    expect(resolveTurnKind(3, true)).toBe('part3')
  })

  it('splits part 2 into the long turn and the rounding-off question', () => {
    expect(resolveTurnKind(2, true)).toBe('part2_long_turn')
    expect(resolveTurnKind(2, false)).toBe('part2_rounding')
  })

  it('falls back to part 1 for an unexpected part number', () => {
    expect(resolveTurnKind(0, false)).toBe('part1')
    expect(resolveTurnKind(99, false)).toBe('part1')
  })
})

describe('recording limits', () => {
  it('stops the part 2 long turn at exactly two minutes', () => {
    expect(RECORDING_LIMITS.part2_long_turn.hardSeconds).toBe(120)
  })

  it('gives the rounding-off question far less than the long turn', () => {
    expect(RECORDING_LIMITS.part2_rounding.hardSeconds).toBeLessThan(
      RECORDING_LIMITS.part2_long_turn.hardSeconds,
    )
  })

  it('lets part 3 run longer than part 1, as the descriptors expect', () => {
    expect(RECORDING_LIMITS.part3.softSeconds).toBeGreaterThan(
      RECORDING_LIMITS.part1.softSeconds,
    )
  })

  it('leaves room to finish a sentence on every turn but the long one', () => {
    for (const kind of ['part1', 'part2_rounding', 'part3'] as const) {
      const { softSeconds, hardSeconds } = RECORDING_LIMITS[kind]
      expect(hardSeconds).toBeGreaterThan(softSeconds)
    }
  })

  it('warns before the long turn is cut, without extending it', () => {
    const { softSeconds, hardSeconds } = RECORDING_LIMITS.part2_long_turn
    expect(softSeconds).toBeLessThan(hardSeconds)
  })

  it('resolves a limit for every turn kind', () => {
    expect(limitForTurn('part1')).toEqual(RECORDING_LIMITS.part1)
    expect(limitForTurn('part3')).toEqual(RECORDING_LIMITS.part3)
  })
})
