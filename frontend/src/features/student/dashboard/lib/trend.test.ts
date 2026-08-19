import { describe, expect, it } from 'vitest'
import { sparklinePoints, trendSummary } from './trend'
import { SPARKLINE_HEIGHT, SPARKLINE_PAD, SPARKLINE_WIDTH } from '@/components/report'

describe('sparklinePoints', () => {
  it('returns an empty list for no values', () => {
    expect(sparklinePoints([])).toEqual([])
  })

  it('places a single point at the left pad', () => {
    const [point] = sparklinePoints([9])
    expect(point.x).toBe(SPARKLINE_PAD)
    expect(point.y).toBe(SPARKLINE_PAD)
  })

  it('maps band 0 to the bottom pad and band 9 to the top pad', () => {
    const [low, high] = sparklinePoints([0, 9])
    expect(low.x).toBe(SPARKLINE_PAD)
    expect(low.y).toBe(SPARKLINE_HEIGHT - SPARKLINE_PAD)
    expect(high.x).toBe(SPARKLINE_WIDTH - SPARKLINE_PAD)
    expect(high.y).toBe(SPARKLINE_PAD)
  })
})

describe('trendSummary', () => {
  it('explains when there is not enough history', () => {
    expect(trendSummary([{ band: 6, date: '2026-01-01' }])).toBe(
      'Not enough attempts to show a trend',
    )
  })

  it('describes direction from first to last band', () => {
    expect(
      trendSummary([
        { band: 6, date: '2026-01-01' },
        { band: 7, date: '2026-02-01' },
      ]),
    ).toBe('2 attempts, 6.0 to 7.0, up')
    expect(
      trendSummary([
        { band: 7, date: '2026-01-01' },
        { band: 6, date: '2026-02-01' },
      ]),
    ).toBe('2 attempts, 7.0 to 6.0, down')
    expect(
      trendSummary([
        { band: 6.5, date: '2026-01-01' },
        { band: 6.5, date: '2026-02-01' },
      ]),
    ).toBe('2 attempts, 6.5 to 6.5, unchanged')
  })
})
