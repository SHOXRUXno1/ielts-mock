import { describe, expect, it } from 'vitest'
import { otherPartPlayingCopy } from './listening-audio-player'

describe('otherPartPlayingCopy', () => {
  it('says which part is on the tape when viewing another part', () => {
    expect(otherPartPlayingCopy(1, 3)).toBe(
      'Part 1 is still playing. Part 3 starts automatically when the recording reaches it.',
    )
  })
})
