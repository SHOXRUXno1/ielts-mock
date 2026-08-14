import { describe, expect, it, vi, afterEach } from 'vitest'
import { formatDuration, relativeTime } from './format'

describe('formatDuration', () => {
  it('formats seconds', () => {
    expect(formatDuration(45)).toBe('45s')
  })

  it('formats minutes', () => {
    expect(formatDuration(12 * 60)).toBe('12m')
  })

  it('formats hours with leftover minutes', () => {
    expect(formatDuration(2 * 3600 + 15 * 60)).toBe('2h 15m')
  })

  it('formats days', () => {
    expect(formatDuration(26 * 3600)).toBe('1d 2h')
  })

  it('handles nullish', () => {
    expect(formatDuration(null)).toBe('—')
    expect(formatDuration(undefined)).toBe('—')
  })
})

describe('relativeTime', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns just now for recent timestamps', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-07-27T12:00:00Z'))
    expect(relativeTime('2026-07-27T11:59:40Z')).toBe('just now')
  })

  it('returns minutes ago', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-07-27T12:00:00Z'))
    expect(relativeTime('2026-07-27T11:55:00Z')).toBe('5m ago')
  })

  it('returns hours ago', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-07-27T12:00:00Z'))
    expect(relativeTime('2026-07-27T10:00:00Z')).toBe('2h ago')
  })

  it('handles empty', () => {
    expect(relativeTime(null)).toBe('—')
  })
})
