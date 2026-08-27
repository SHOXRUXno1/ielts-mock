/**
 * Header clock flags. Kept pure so the ticking chrome can stay a sibling of
 * the exam body — Speaking must not subscribe to remainingSec.
 */
export function examHeaderClockVisibility(opts: {
  isPreview: boolean
  hasAttempt: boolean
  hasProgress: boolean
  isSpeaking: boolean
  remainingMs: number | null
  remainingSec: number
}): { showAiPaced: boolean; showCountdown: boolean } {
  const speakingChrome = opts.isSpeaking && !opts.isPreview
  return {
    showAiPaced: speakingChrome && opts.remainingSec > 300,
    showCountdown:
      !opts.isPreview &&
      opts.hasAttempt &&
      opts.hasProgress &&
      opts.remainingMs != null &&
      (!speakingChrome || opts.remainingSec <= 300),
  }
}
