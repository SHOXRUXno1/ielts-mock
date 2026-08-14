import type { Phase } from '../types/phase'

/** Phases where the examiner session is running — init must not clobber these. */
const LIVE_PHASES = new Set<Phase>([
  'thinking',
  'playing',
  'ready',
  'recording',
  'transcribing',
  'prep',
  'scoring',
])

export function isLiveSpeakingPhase(phase: Phase): boolean {
  return LIVE_PHASES.has(phase)
}
