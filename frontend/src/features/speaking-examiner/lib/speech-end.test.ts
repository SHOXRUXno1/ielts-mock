import { describe, expect, it, vi } from 'vitest'
import {
  END_BACKSTOP_MARGIN_MS,
  END_MARGIN_AFTER_SPEECH_MS,
  SILENCE_EARLIEST_FRACTION,
  endTimerDelayMs,
  muteLiveAudioElement,
  silenceAudioElement,
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
  const farEnough = {
    audioSent: true,
    sendComplete: true,
    speakingStartedAt: NOW,
    durationMs: FOUR_SECOND_ANSWER,
    now: NOW + FOUR_SECOND_ANSWER * SILENCE_EARLIEST_FRACTION,
  }

  it('ignores the silence left by clearing the previous turn', () => {
    expect(silenceEndsTurn({ ...farEnough, sendComplete: false })).toBe(false)
  })

  it('accepts silence only once most of the utterance should have been heard', () => {
    expect(silenceEndsTurn(farEnough)).toBe(true)
  })

  it('ignores a pause between words', () => {
    // Ending here is what leaves a leftover voice: the session moves on and
    // the rest of the sentence keeps playing over the candidate.
    expect(
      silenceEndsTurn({
        ...farEnough,
        now: NOW + FOUR_SECOND_ANSWER * 0.3,
      }),
    ).toBe(false)
  })

  it('does not trust silence when the avatar never reported starting', () => {
    expect(silenceEndsTurn({ ...farEnough, speakingStartedAt: null })).toBe(
      false,
    )
  })

  it('ignores silence when there is no turn in flight at all', () => {
    expect(silenceEndsTurn({ ...farEnough, audioSent: false })).toBe(false)
  })
})

describe('silencing leftover playback', () => {
  it('mutes, pauses and rewinds the element', () => {
    const el = { pause: vi.fn(), volume: 1, currentTime: 3.2 }

    silenceAudioElement(el)

    expect(el.volume).toBe(0)
    expect(el.pause).toHaveBeenCalledOnce()
    expect(el.currentTime).toBe(0)
  })

  it('does nothing when there is no element', () => {
    expect(() => silenceAudioElement(null)).not.toThrow()
  })

  it('ducks a live stream without pausing it', () => {
    const el = { pause: vi.fn(), volume: 1, currentTime: 1.4 }

    muteLiveAudioElement(el)

    expect(el.volume).toBe(0)
    expect(el.pause).not.toHaveBeenCalled()
    expect(el.currentTime).toBe(1.4)
  })
})
