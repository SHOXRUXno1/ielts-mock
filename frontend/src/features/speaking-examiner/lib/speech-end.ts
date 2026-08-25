/**
 * Deciding when the examiner has finished speaking.
 *
 * Simli reports the avatar going quiet, and that report is the only thing that
 * knows when the mouth actually stops moving. Everything here is the fallback
 * for when it does not arrive, and the fallback has to lean late: ending a turn
 * early opens the microphone over the examiner's own voice, and whatever the
 * candidate says into that gap is what gets scored as their answer.
 */

/** Grace on top of the audio's own length, once we know when it began. */
export const END_MARGIN_AFTER_SPEECH_MS = 1500

/**
 * Earliest fraction of the utterance at which a report of silence may mean
 * the examiner has finished. Before that it is a pause between words — and
 * ending there leaves the rest of the sentence playing over the candidate.
 */
export const SILENCE_EARLIEST_FRACTION = 0.75

/**
 * Grace when the avatar never reported starting, leaving the moment we finished
 * handing over the bytes as the only reference. WebRTC can hold those in a
 * jitter buffer for some time before a word is heard, hence the wider
 * allowance — the previous half-second expired mid-sentence often enough that
 * candidates were cut off by their own microphone.
 */
export const END_BACKSTOP_MARGIN_MS = 5000

type EndTimerArgs = {
  /** Length of the audio handed to the avatar. */
  durationMs: number
  /** When the avatar reported starting, or null if it never did. */
  speakingStartedAt: number | null
  /** When the last chunk was handed over — the fallback reference point. */
  sendCompletedAt: number
  now: number
}

/**
 * How long to keep waiting before giving up on a report of silence.
 *
 * Both reference points are fixed moments rather than "now", so re-reading this
 * as the wait runs down converges instead of sliding the deadline forward.
 */
export function endTimerDelayMs({
  durationMs,
  speakingStartedAt,
  sendCompletedAt,
  now,
}: EndTimerArgs): number {
  const margin =
    speakingStartedAt === null
      ? END_BACKSTOP_MARGIN_MS
      : END_MARGIN_AFTER_SPEECH_MS
  const anchor = speakingStartedAt ?? sendCompletedAt
  return Math.max(0, anchor + durationMs + margin - now)
}

type SilenceArgs = {
  /** This turn's audio has been handed to the avatar. */
  audioSent: boolean
  /** Every chunk of it, not just the first. */
  sendComplete: boolean
  /** When the avatar reported starting, or null if it never did. */
  speakingStartedAt?: number | null
  /** Length of the audio handed to the avatar. */
  durationMs?: number
  now?: number
}

/**
 * Whether a report of silence is about the turn we are waiting on.
 *
 * Each turn starts by clearing the avatar's buffer, and draining the previous
 * turn out of it is itself reported as silence. Taken at face value that ends
 * the new turn before its first word, so silence only counts once every chunk
 * has been handed over.
 *
 * After that, a pause between words is still reported as silence. Ending there
 * is what leaves a leftover voice and a leftover mouth: the session moves on,
 * the microphone opens, and the rest of the sentence keeps playing. Silence
 * may close the turn only once most of the utterance should already have been
 * heard; the duration timer is the authority until then.
 */
export function silenceEndsTurn({
  audioSent,
  sendComplete,
  speakingStartedAt = null,
  durationMs = 0,
  now = 0,
}: SilenceArgs): boolean {
  if (!audioSent || !sendComplete) return false
  if (speakingStartedAt === null || durationMs <= 0) return false
  return now - speakingStartedAt >= durationMs * SILENCE_EARLIEST_FRACTION
}

type MuteableAudio = {
  pause: () => void
  volume: number
  currentTime: number
}

/**
 * Stop a leftover utterance we ourselves created (`new Audio(...)`).
 *
 * Do not use this on Simli's WebRTC element: `pause()` there is permanent —
 * the next turn turns the volume back up and nobody ever calls `play()`, so
 * the examiner appears to speak and no sound comes out.
 */
export function silenceAudioElement(el: MuteableAudio | null | undefined): void {
  if (!el) return
  el.volume = 0
  el.pause()
  try {
    el.currentTime = 0
  } catch {
    // Some remote streams throw on seek; muting is enough for those.
  }
}

/** Duck a live stream without pausing it, so the next `play()` is not required. */
export function muteLiveAudioElement(
  el: { volume: number } | null | undefined,
): void {
  if (!el) return
  el.volume = 0
}
