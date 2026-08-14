import { describe, expect, it } from 'vitest'
import { parseSectionExpired, toExpiredInfo } from './section-expired'

describe('parseSectionExpired', () => {
  it('parses structured 409 detail', () => {
    const err = {
      response: {
        status: 409,
        data: {
          detail: {
            code: 'SECTION_EXPIRED',
            message: 'Section time expired',
            sealed_at: '2026-01-01T12:00:00Z',
            next_section: 'reading',
          },
        },
      },
    }
    expect(parseSectionExpired(err)).toEqual({
      code: 'SECTION_EXPIRED',
      message: 'Section time expired',
      sealed_at: '2026-01-01T12:00:00Z',
      next_section: 'reading',
    })
  })

  it('returns null for plain string conflict', () => {
    const err = {
      response: {
        status: 409,
        data: { detail: 'Section already completed' },
      },
    }
    expect(parseSectionExpired(err)).toBeNull()
  })

  it('maps next_section via toExpiredInfo', () => {
    const info = toExpiredInfo(
      {
        code: 'SECTION_EXPIRED',
        message: 'expired',
        sealed_at: null,
        next_section: 'writing',
      },
      'reading',
    )
    expect(info.from).toBe('reading')
    expect(info.next).toBe('writing')
  })
})
