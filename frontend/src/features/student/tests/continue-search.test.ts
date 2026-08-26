import { describe, expect, it } from 'vitest'
import { continueTakeSearch } from './continue-search'

describe('continueTakeSearch', () => {
  it('resumes the live section instead of always listening', () => {
    expect(continueTakeSearch('a1', 'writing')).toEqual({
      resume: 'a1',
      section: 'writing',
      part: '1',
    })
  })

  it('omits part on speaking', () => {
    expect(continueTakeSearch('a1', 'speaking')).toEqual({
      resume: 'a1',
      section: 'speaking',
      part: undefined,
    })
  })

  it('falls back to listening when the section is missing or unknown', () => {
    expect(continueTakeSearch('a1', null).section).toBe('listening')
    expect(continueTakeSearch('a1', 'cambridge').section).toBe('listening')
  })
})
