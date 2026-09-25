/**
 * Per-answer recording limits for the AI Speaking examiner.
 *
 * A live examiner paces the exam by listening and moving on; an automated one
 * needs an explicit ceiling or a single verbose candidate eats the whole
 * session budget. The ceiling is therefore a substitute for the examiner's
 * judgement, not an exam rule — real IELTS has no per-answer clock.
 *
 * Two thresholds per turn:
 *  - `softSeconds` surfaces a wrap-up cue so the candidate can close the
 *    sentence they are in.
 *  - `hardSeconds` actually stops the recorder.
 *
 * Cutting mid-clause hands the scorer a truncated transcript and drags down
 * Fluency & Coherence for the candidates who develop their answers most, so
 * the two thresholds must never be equal outside Part 2.
 */

/**
 * Which turn the candidate is answering. Part 2 needs two entries: the long
 * turn and the short rounding-off question that follows it both report
 * `part: 2`, but a yes/no follow-up has no business holding a two-minute slot.
 */
export type SpeakingTurnKind =
  | 'part1'
  | 'part2_long_turn'
  | 'part2_rounding'
  | 'part3'

export type RecordingLimit = {
  /** Wrap-up cue appears; recording continues. */
  softSeconds: number
  /** Recorder stops here. */
  hardSeconds: number
}

/**
 * Part 1 — real Part 1 runs 4-5 min over ~12 questions, so a good answer is
 * 20-40 s. This exam compresses Part 1 to 5 questions, so 45 s each lands the
 * section on the same 4-5 min as the original.
 *
 * Part 2 — the official long turn is 1-2 min and the examiner stops the
 * candidate at two minutes, so the hard stop stays at exactly 120 s. The cue
 * at 105 s only warns; it does not extend the turn.
 *
 * Part 2 rounding — "Did you enjoy that?" is a yes/no follow-up.
 *
 * Part 3 — extended abstract reasoning is what the band descriptors reward
 * here, and band 7+ answers routinely run 60-90 s.
 */
export const RECORDING_LIMITS: Record<SpeakingTurnKind, RecordingLimit> = {
  part1: { softSeconds: 45, hardSeconds: 60 },
  part2_long_turn: { softSeconds: 105, hardSeconds: 120 },
  part2_rounding: { softSeconds: 30, hardSeconds: 40 },
  part3: { softSeconds: 90, hardSeconds: 105 },
}

/** Countdown stays hidden until this much time is left. */
export const COUNTDOWN_VISIBLE_SECONDS = 10

/**
 * Client-side voice-activity gate — rejects near-silent recordings before they
 * reach STT. Whisper hallucinates plausible-sounding text on silence and room
 * tone (its training set ends every video with "Thank you for watching",
 * "Please subscribe", etc.), so keeping empty audio out of the pipeline
 * eliminates most made-up answers at the source.
 *
 * A recording is treated as silence — and the candidate is asked to speak
 * again — when ANY of:
 *   - total duration is shorter than MIN_DURATION_MS
 *   - peak RMS never exceeded RMS_THRESHOLD_DBFS
 *   - cumulative time above the threshold is less than MIN_ACTIVE_MS
 *
 * Thresholds are calibrated for a laptop mic in a quiet-to-moderate room. A
 * quiet speaker with visible mic levels (top 2-3 bars) sits comfortably above
 * the floor; hands-off silence with background hum reads roughly -55 dBFS.
 */
export const VOICE_GATE = {
  RMS_THRESHOLD_DBFS: -50,
  MIN_ACTIVE_MS: 300,
  MIN_DURATION_MS: 800,
} as const

export function resolveTurnKind(
  currentPart: number,
  isPart2LongTurn: boolean,
): SpeakingTurnKind {
  if (currentPart === 2) {
    return isPart2LongTurn ? 'part2_long_turn' : 'part2_rounding'
  }
  if (currentPart === 3) return 'part3'
  return 'part1'
}

export function limitForTurn(kind: SpeakingTurnKind): RecordingLimit {
  return RECORDING_LIMITS[kind] ?? RECORDING_LIMITS.part1
}
