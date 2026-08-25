import { describe, expect, it } from 'vitest'
import {
  END_BACKSTOP_MARGIN_MS,
  END_MARGIN_AFTER_SPEECH_MS,
  endTimerDelayMs,
  silenceEndsTurn,
} from './speech-end'

const NOW = 1_000_000
const FOUR_SECOND_ANSWER = 4000

describe('waiting for the examiner to stop talking', () => {
  it('measures from when the avatar actually started, not from now', () => {
    expect(
      endTimerDelayMs({
        durationMs: FOUR_SECOND_ANSWER,
        speakingStartedAt: NOW - 500,
        sendCompletedAt: NOW - 800,
        now: NOW,
      }),
    ).toBe(FOUR_SECOND_ANSWER - 500 + END_MARGIN_AFTER_SPEECH_MS)
  })

  it('falls back to the last chunk sent, and waits far longer for it', () => {
    expect(
      endTimerDelayMs({
        durationMs: FOUR_SECOND_ANSWER,
        speakingStartedAt: null,
        sendCompletedAt: NOW,
        now: NOW,
      }),
    ).toBe(FOUR_SECOND_ANSWER + END_BACKSTOP_MARGIN_MS)
  })

  it('counts down rather than sliding the deadline forward', () => {
    // Re-read as the wait runs down, this has to converge on zero: the timer
    // consults it again when it expires, and an answer that always measures
    // from the present moment would keep the turn open for ever.
    const args = {
      durationMs: FOUR_SECOND_ANSWER,
      speakingStartedAt: null,
      sendCompletedAt: NOW,
    }

    const atStart = endTimerDelayMs({ ...args, now: NOW })
    const later = endTimerDelayMs({ ...args, now: NOW + 3000 })

    expect(later).toBe(atStart - 3000)
    expect(endTimerDelayMs({ ...args, now: NOW + atStart })).toBe(0)
  })

  it('never asks for a wait in the past', () => {
    expect(
      endTimerDelayMs({
        durationMs: FOUR_SECOND_ANSWER,
        speakingStartedAt: NOW - 60_000,
        sendCompletedAt: NOW - 60_000,
        now: NOW,
      }),
    ).toBe(0)
  })

  it('leaves more room than the half second that used to cut turns short', () => {
    // The deadline this replaces was the audio's length plus 500ms, measured
    // from the last byte sent rather than the first word heard. A turn that
    // took a moment to come out of the jitter buffer expired mid-sentence,
    // opening the microphone over the examiner's own voice.
    const oldDeadline = FOUR_SECOND_ANSWER + 500

    expect(
      endTimerDelayMs({
        durationMs: FOUR_SECOND_ANSWER,
        speakingStartedAt: null,
        sendCompletedAt: NOW,
        now: NOW,
      }),
    ).toBeGreaterThan(oldDeadline)
  })

  it('extends when the avatar turns out to have started very late', () => {
    // The wait is set when the last chunk goes out. If the avatar only reports
    // beginning once most of that wait is gone — a slow connection holding the
    // audio in its jitter buffer — the real end is past the original deadline.
    const startedLate = NOW + 6000

    const asScheduled = endTimerDelayMs({
      durationMs: FOUR_SECOND_ANSWER,
      speakingStartedAt: null,
      sendCompletedAt: NOW,
      now: NOW,
    })
    const onceKnown = endTimerDelayMs({
      durationMs: FOUR_SECOND_ANSWER,
      speakingStartedAt: startedLate,
      sendCompletedAt: NOW,
      now: NOW + asScheduled,
    })

    expect(onceKnown).toBeGreaterThan(0)
  })
})

describe('reading a report of silence', () => {
  it('ignores the silence left by clearing the previous turn', () => {
    expect(silenceEndsTurn({ audioSent: true, sendComplete: false })).toBe(false)
  })

  it('accepts silence once the whole answer has been handed over', () => {
    expect(silenceEndsTurn({ audioSent: true, sendComplete: true })).toBe(true)
  })

  it('ignores silence when there is no turn in flight at all', () => {
    expect(silenceEndsTurn({ audioSent: false, sendComplete: true })).toBe(false)
  })
})
