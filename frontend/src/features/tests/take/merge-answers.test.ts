import { describe, expect, it } from 'vitest'
import { mergeAnswersServerWins } from './merge-answers'

describe('mergeAnswersServerWins', () => {
  it('lets server overwrite overlapping question ids', () => {
    const local = {
      sec1: { q1: { answer: 'local' }, q2: { answer: 'only-local' } },
    }
    const server = {
      sec1: { q1: { answer: 'server' } },
    }
    expect(mergeAnswersServerWins(local, server)).toEqual({
      sec1: {
        q1: { answer: 'server' },
        q2: { answer: 'only-local' },
      },
    })
  })

  it('keeps server-only sections', () => {
    const merged = mergeAnswersServerWins(
      { a: { q: { answer: '1' } } },
      { b: { q: { answer: '2' } } },
    )
    expect(merged.a?.q).toEqual({ answer: '1' })
    expect(merged.b?.q).toEqual({ answer: '2' })
  })
})
