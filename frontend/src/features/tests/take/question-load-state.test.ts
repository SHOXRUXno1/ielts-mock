import { describe, expect, it } from 'vitest'
import { hasLoadedQuestions } from './question-load-state'

describe('hasLoadedQuestions', () => {
  it('keeps an unrequested section in loading state', () => {
    expect(hasLoadedQuestions({}, 'listening-2')).toBe(false)
  })

  it('treats a fetched empty section as loaded', () => {
    expect(hasLoadedQuestions({ 'listening-2': [] }, 'listening-2')).toBe(true)
  })
})
