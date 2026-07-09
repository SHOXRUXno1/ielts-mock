import { describe, expect, it } from 'vitest'
import {
  isCueCardTurn,
  previewLiveTurnText,
  shouldTruncateLiveTurn,
} from './format-live-turn'

describe('formatLiveTurn', () => {
  it('detects cue card turns', () => {
    expect(isCueCardTurn('Describe a journey. You should say: where you went')).toBe(
      true,
    )
    expect(isCueCardTurn('What do you do in your free time?')).toBe(false)
  })

  it('truncates long turns', () => {
    const long = 'a'.repeat(200)
    expect(shouldTruncateLiveTurn(long)).toBe(true)
    expect(previewLiveTurnText(long).endsWith('…')).toBe(true)
    expect(previewLiveTurnText(long).length).toBeLessThan(long.length)
  })
})
