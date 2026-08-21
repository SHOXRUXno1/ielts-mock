import { afterEach, describe, expect, it } from 'vitest'
import {
  clearScoreReveal,
  hasScoreReveal,
  markScoreReveal,
} from './score-reveal-flag'

describe('score-reveal-flag', () => {
  afterEach(() => {
    sessionStorage.clear()
  })

  it('remembers a pending reveal per attempt', () => {
    expect(hasScoreReveal('a1')).toBe(false)
    markScoreReveal('a1')
    expect(hasScoreReveal('a1')).toBe(true)
    expect(hasScoreReveal('a2')).toBe(false)
    clearScoreReveal('a1')
    expect(hasScoreReveal('a1')).toBe(false)
  })
})
