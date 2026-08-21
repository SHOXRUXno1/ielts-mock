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

  it('passes reveal through when truthy', () => {
    expect(parseResultSearch({ reveal: true })).toEqual({ reveal: true })
    expect(parseResultSearch({ reveal: 1 })).toEqual({ reveal: true })
    expect(parseResultSearch({ reveal: '1' })).toEqual({ reveal: true })
    expect(parseResultSearch({ reveal: 'true' })).toEqual({ reveal: true })
  })

  it('drops reveal when falsy or missing', () => {
    expect(parseResultSearch({ reveal: false })).toEqual({})
    expect(parseResultSearch({ reveal: 0 })).toEqual({})
    expect(parseResultSearch({ reveal: 'no' })).toEqual({})
  })

  it('combines tab and reveal', () => {
    expect(parseResultSearch({ tab: 'listening', reveal: '1' })).toEqual({
      tab: 'listening',
      reveal: true,
    })
  })
})
