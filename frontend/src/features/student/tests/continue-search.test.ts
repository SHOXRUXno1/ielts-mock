import { afterEach, describe, expect, it } from 'vitest'
import { continueTakeSearch } from './continue-search'
import { lsKeyForAttempt } from '@/features/tests/take/constants'

describe('continueTakeSearch', () => {
  afterEach(() => {
    localStorage.clear()
  })

  it('resumes the live section instead of always listening', () => {
    expect(continueTakeSearch('a1', 'writing')).toEqual({
      resume: 'a1',
      section: 'writing',
      part: '1',
    })
  })

  it('uses the server part when local storage is empty', () => {
    expect(continueTakeSearch('a1', 'listening', 3)).toEqual({
      resume: 'a1',
      section: 'listening',
      part: '3',
    })
  })

  it('prefers the last viewed part in local storage', () => {
    localStorage.setItem(
      lsKeyForAttempt('a1'),
      JSON.stringify({ resume: { section: 'reading', part: '4' } }),
    )
    expect(continueTakeSearch('a1', 'reading', 1)).toEqual({
      resume: 'a1',
      section: 'reading',
      part: '4',
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
