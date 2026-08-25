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
 * Grace when the avatar never reported starting, leaving the moment we finished
 * handing over the bytes as the only reference. Wider than the half-second
 * that used to cut people off, but not so wide that the microphone sits
 * closed for seconds after the examiner has already gone quiet.
 */
export const END_BACKSTOP_MARGIN_MS = 2000

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
}

/**
 * Whether a report of silence is about the turn we are waiting on.
 *
 * Each turn starts by clearing the avatar's buffer, and draining the previous
 * turn out of it is itself reported as silence. Taken at face value that ends
 * the new turn before its first word, so silence only counts once every chunk
 * has been handed over.
 */
export function silenceEndsTurn({ audioSent, sendComplete }: SilenceArgs): boolean {
  return audioSent && sendComplete
}
