import { describe, expect, it } from 'vitest'
import { examHeaderClockVisibility } from './exam-header-clock'

describe('examHeaderClockVisibility', () => {
  it('hides the countdown on the Speaking readiness gate (no deadline)', () => {
    expect(
      examHeaderClockVisibility({
        isPreview: false,
        hasAttempt: true,
        hasProgress: true,
        isSpeaking: true,
        remainingMs: null,
        remainingSec: 0,
      }),
    ).toEqual({ showAiPaced: false, showCountdown: false })
  })

  it('shows AI-paced when Speaking still has more than 5 minutes', () => {
    expect(
      examHeaderClockVisibility({
        isPreview: false,
        hasAttempt: true,
        hasProgress: true,
        isSpeaking: true,
        remainingMs: 20 * 60 * 1000,
        remainingSec: 1200,
      }),
    ).toEqual({ showAiPaced: true, showCountdown: false })
  })

  it('shows the safety-cap countdown when Speaking is under 5 minutes', () => {
    expect(
      examHeaderClockVisibility({
        isPreview: false,
        hasAttempt: true,
        hasProgress: true,
        isSpeaking: true,
        remainingMs: 4 * 60 * 1000,
        remainingSec: 240,
      }),
    ).toEqual({ showAiPaced: false, showCountdown: true })
  })

  it('hides both clocks in preview', () => {
    expect(
      examHeaderClockVisibility({
        isPreview: true,
        hasAttempt: true,
        hasProgress: true,
        isSpeaking: false,
        remainingMs: 10 * 60 * 1000,
        remainingSec: 600,
      }),
    ).toEqual({ showAiPaced: false, showCountdown: false })
  })

  it('always shows the countdown for Listening / Reading / Writing', () => {
    expect(
      examHeaderClockVisibility({
        isPreview: false,
        hasAttempt: true,
        hasProgress: true,
        isSpeaking: false,
        remainingMs: 10 * 60 * 1000,
        remainingSec: 600,
      }),
    ).toEqual({ showAiPaced: false, showCountdown: true })
  })
})
