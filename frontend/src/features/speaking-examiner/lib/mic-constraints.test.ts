import { describe, expect, it } from 'vitest'
import { SPEAKING_AUDIO_CONSTRAINTS } from './mic-constraints'

/**
 * These are regression guards, not documentation of a shape. Each test defends
 * one behavioural claim about the microphone the candidate is recorded on;
 * dropping any of them silently reintroduces a specific bug on cheap headsets.
 */
describe('SPEAKING_AUDIO_CONSTRAINTS', () => {
  const audio = SPEAKING_AUDIO_CONSTRAINTS.audio

  it('asks the browser for an audio track with settings, not a plain "on" boolean', () => {
    // Passing { audio: true } forgets every DSP toggle below. This is the
    // shape guard that keeps the fields we care about reachable at all.
    expect(typeof audio).toBe('object')
    expect(audio).not.toBeNull()
  })

  it('turns on auto gain — the single fix for candidates who drift between whisper and shout', () => {
    // Removing this reopens the original complaint: a cheap headset without
    // AGC gives Whisper a signal that swings between clipping and silence,
    // and the model reads the quiet stretches as pauses that never happened.
    expect((audio as MediaTrackConstraints).autoGainControl).toBe(true)
  })

  it('keeps echo cancellation and noise suppression on so a laptop speaker sitting is transcribable at all', () => {
    // Both were already here before the AGC fix; the test exists so a future
    // "clean up unused constraints" pass cannot quietly drop them.
    expect((audio as MediaTrackConstraints).echoCancellation).toBe(true)
    expect((audio as MediaTrackConstraints).noiseSuppression).toBe(true)
  })

  it('requests a single audio channel — every STT engine downmixes anyway, and stereo from a mono capsule is duplicated bytes', () => {
    expect((audio as MediaTrackConstraints).channelCount).toBe(1)
  })

  it('hints 16 kHz — the sample rate Whisper and Chirp use internally', () => {
    // The browser is allowed to ignore this, so the effect is opportunistic;
    // the test pins the intent so a "let the driver decide" refactor cannot
    // remove the hint without a deliberate decision.
    expect((audio as MediaTrackConstraints).sampleRate).toBe(16000)
  })
})
