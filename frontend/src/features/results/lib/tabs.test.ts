import { describe, expect, it } from 'vitest'
import { parseResultSearch } from './tabs'

describe('parseResultSearch', () => {
  it('returns an empty object for unknown params', () => {
    expect(parseResultSearch({})).toEqual({})
    expect(parseResultSearch({ tab: 'nope' })).toEqual({})
  })

  it('keeps known tabs', () => {
    expect(parseResultSearch({ tab: 'writing' })).toEqual({ tab: 'writing' })
  })

  it('ignores leftover reveal query params', () => {
    expect(parseResultSearch({ reveal: true })).toEqual({})
    expect(parseResultSearch({ tab: 'listening', reveal: '1' })).toEqual({
      tab: 'listening',
    })
  })
})
