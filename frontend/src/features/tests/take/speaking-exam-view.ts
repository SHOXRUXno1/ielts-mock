import type { SectionState } from '@/lib/api/section-progress'

export type SpeakingExamView = 'loading' | 'gate' | 'session'

/**
 * Live-exam Speaking must not mount the examiner until progress is known.
 * A first paint with `stateOf('speaking') === null` used to render the
 * auto-starting session, then flip to the readiness gate — that remount
 * loop is React error #185 on resume.
 */
export function resolveSpeakingExamView(opts: {
  isLiveExam: boolean
  progressLoaded: boolean
  speakingState: SectionState | null
}): SpeakingExamView {
  if (!opts.isLiveExam) return 'session'
  if (!opts.progressLoaded) return 'loading'
  if (opts.speakingState === 'not_started') return 'gate'
  return 'session'
}
