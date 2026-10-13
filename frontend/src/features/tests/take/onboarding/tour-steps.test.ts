import { describe, expect, it } from 'vitest'
import { stepsForSection } from './tour-steps'

describe('stepsForSection', () => {
  it('keeps desktop question guidance anchored to the question pane', () => {
    expect(stepsForSection('listening')[2].target).toBe(
      '[data-tour="listening-questions"]'
    )
    expect(stepsForSection('reading')[2].target).toBe(
      '[data-tour="reading-questions"]'
    )
  })

  it('anchors mobile question guidance to the visible Questions tab', () => {
    const listeningSteps = stepsForSection('listening', false)
    const readingSteps = stepsForSection('reading', false)

    expect(listeningSteps).toHaveLength(5)
    expect(readingSteps).toHaveLength(5)
    expect(listeningSteps[2].target).toBe(
      '[data-tour="listening-questions-tab"]'
    )
    expect(readingSteps[2].target).toBe('[data-tour="reading-questions-tab"]')
  })

  it('uses readiness-screen targets before live Speaking starts', () => {
    const steps = stepsForSection('speaking', false, true)

    expect(steps).toHaveLength(3)
    expect(steps[1].target).toBe('[data-tour="speaking-mic-check"]')
    expect(steps[2].target).toBe('[data-tour="speaking-start"]')
  })

  it('uses writing-specific guidance in the Writing tour', () => {
    expect(stepsForSection('writing')[0].content).toContain(
      'Plan what you want to write'
    )
  })
})
