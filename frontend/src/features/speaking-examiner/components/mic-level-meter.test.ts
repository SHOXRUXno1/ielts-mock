import { describe, expect, it } from 'vitest'

function averageLevel(levels: number[]): number {
  return levels.length > 0
    ? Math.round(levels.reduce((sum, level) => sum + level, 0) / levels.length)
    : 0
}

describe('MicLevelMeter average', () => {
  it('stays within 0-100 when levels are 0-100', () => {
    expect(averageLevel([50, 50, 50])).toBe(50)
    expect(averageLevel([100, 100])).toBe(100)
    expect(averageLevel([0, 0])).toBe(0)
  })
})
