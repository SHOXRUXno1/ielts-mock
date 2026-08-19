import { describe, expect, it } from 'vitest'
import { BAND_MAX, BAND_SEGMENT_COUNT, bandPercent, bandSegments, bandTone, formatBand } from './band'

describe('formatBand', () => {
  it('returns an em dash for empty values', () => {
    expect(formatBand(null)).toBe('—')
    expect(formatBand(undefined)).toBe('—')
  })

  it('formats whole and half bands to one decimal', () => {
    expect(formatBand(7)).toBe('7.0')
    expect(formatBand(6.5)).toBe('6.5')
  })
})

describe('bandPercent', () => {
  it('maps a band onto a 0–100 scale of BAND_MAX', () => {
    expect(bandPercent(null)).toBe(0)
    expect(bandPercent(0)).toBe(0)
    expect(bandPercent(BAND_MAX)).toBe(100)
    expect(bandPercent(4.5)).toBe(50)
  })

  it('clamps out-of-range values', () => {
    expect(bandPercent(12)).toBe(100)
    expect(bandPercent(-1)).toBe(0)
  })
})

describe('bandSegments', () => {
  it('returns zero for empty bands', () => {
    expect(bandSegments(null)).toBe(0)
    expect(bandSegments(undefined)).toBe(0)
  })

  it('maps half-band steps onto 18 segments', () => {
    expect(bandSegments(0)).toBe(0)
    expect(bandSegments(0.5)).toBe(1)
    expect(bandSegments(4.5)).toBe(9)
    expect(bandSegments(7)).toBe(14)
    expect(bandSegments(9)).toBe(BAND_SEGMENT_COUNT)
  })

  it('clamps out-of-range values', () => {
    expect(bandSegments(12)).toBe(BAND_SEGMENT_COUNT)
    expect(bandSegments(-2)).toBe(0)
  })
})

describe('bandTone', () => {
  it('classifies bands by IELTS thresholds', () => {
    expect(bandTone(null)).toBe('empty')
    expect(bandTone(7)).toBe('strong')
    expect(bandTone(5.5)).toBe('fair')
    expect(bandTone(5)).toBe('weak')
  })
})
