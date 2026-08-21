import { describe, expect, it } from 'vitest'
import { groupAwareScrollTop } from './flash-question'

describe('groupAwareScrollTop', () => {
  it('scrolls a short group to the top of the pane (keeps Questions 37–40 visible)', () => {
    // Pane is 600px. Group is 420px and currently starts 80px above the pane.
    expect(
      groupAwareScrollTop({
        paneScrollTop: 400,
        paneTop: 100,
        paneHeight: 600,
        questionTop: 480,
        groupTop: 20,
        groupHeight: 420,
        padding: 16,
      }),
    ).toBe(400 + (20 - 100) - 16)
  })

  it('does not center a late question when the group fits', () => {
    const top = groupAwareScrollTop({
      paneScrollTop: 800,
      paneTop: 80,
      paneHeight: 700,
      questionTop: 520,
      groupTop: 90,
      groupHeight: 380,
      padding: 16,
    })
    // Group top (90) is used, not the question (520).
    expect(top).toBe(800 + (90 - 80) - 16)
    expect(top).not.toBe(800 + (520 - 80) - 16)
  })

  it('scrolls the question itself when the group is taller than the pane', () => {
    expect(
      groupAwareScrollTop({
        paneScrollTop: 200,
        paneTop: 80,
        paneHeight: 500,
        questionTop: 640,
        groupTop: 40,
        groupHeight: 900,
        padding: 16,
      }),
    ).toBe(200 + (640 - 80) - 16)
  })

  it('aligns the question when there is no group', () => {
    expect(
      groupAwareScrollTop({
        paneScrollTop: 0,
        paneTop: 0,
        paneHeight: 500,
        questionTop: 240,
        padding: 16,
      }),
    ).toBe(224)
  })
})
