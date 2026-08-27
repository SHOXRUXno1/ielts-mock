import { useCallback, useMemo } from 'react'
import { ExamHeader } from '../components/take/exam-header'
import { TimeoutDialog } from '../components/take/timeout-dialog'
import type { SectionType } from '../data/schema'
import { examHeaderClockVisibility } from './exam-header-clock'
import { nextUnlockableType } from './section-order'
import { useTakeTest } from './take-test-context'
import { useTakeTestTimer } from './take-test-timer-context'
import type { TimeoutDialogInfo } from './use-section-expiry-dialog'
import { useSectionTimeWarnings } from './use-section-time-warnings'
import { useSectionTimeout } from './use-section-timeout'
import { useTestNavigation } from './use-test-navigation'

type ExamTimerChromeProps = {
  totalAnswered: number
  totalQuestions: number
  finishDisabled: boolean
  onFinishSection: () => void
  onSwitchType: (type: SectionType) => void
  timeoutDialog: TimeoutDialogInfo | null
  timeoutCountdown: number | null
  clearTimeoutDialog: () => void
  peekTimeoutNext: () => SectionType | null
  onTimeoutExhausted: () => void
}

/**
 * The only exam-chrome subscriber to the 2Hz countdown.
 *
 * Must stay a *sibling* of the section body (Speaking). If this hook lived on
 * the parent that wraps `<main>`, every tick would re-render WebRTC.
 */
export function ExamTimerChrome({
  totalAnswered,
  totalQuestions,
  finishDisabled,
  onFinishSection,
  onSwitchType,
  timeoutDialog,
  timeoutCountdown,
  clearTimeoutDialog,
  peekTimeoutNext,
  onTimeoutExhausted,
}: ExamTimerChromeProps) {
  const ctx = useTakeTest()
  const nav = useTestNavigation()
  const { remainingMs, remainingSec, timerExpired } = useTakeTestTimer()

  const {
    test,
    isPreview,
    isPractice,
    presentTypes,
    answers,
    sortedSections,
    attemptId,
    progress,
    sealedTypes,
    flushBeforeNavigate,
    sealSection,
    enterSection,
    reportSectionExpired,
    activeSectionType,
    stateOf,
    submitTest,
    isSubmitting,
    practiceScope,
  } = ctx

  const timedSectionType = activeSectionType ?? nav.currentType
  const unlockableType = nextUnlockableType(
    presentTypes,
    stateOf,
    activeSectionType,
  )

  const sectionStates = useMemo(() => {
    const map: Partial<
      Record<SectionType, { state: string; sealedAt?: string | null }>
    > = {}
    for (const s of progress?.sections ?? []) {
      map[s.section_type as SectionType] = {
        state: s.state,
        sealedAt: s.sealed_at,
      }
    }
    for (const t of sealedTypes) {
      if (!map[t]) map[t] = { state: 'sealed' }
    }
    return map
  }, [progress, sealedTypes])

  const { showAiPaced, showCountdown } = examHeaderClockVisibility({
    isPreview,
    hasAttempt: !!attemptId,
    hasProgress: !!progress,
    isSpeaking: nav.currentType === 'speaking',
    remainingMs,
    remainingSec,
  })

  useSectionTimeWarnings({
    remainingMs,
    sectionType: timedSectionType,
    enabled: !isPreview && !!attemptId,
    suppressFiveMin: isPractice && practiceScope === 'part',
  })

  const { handleContinue: handleTimeoutContinue } = useSectionTimeout({
    enabled: !isPreview && !!attemptId,
    timerExpired,
    deadlineType: activeSectionType,
    expiredType: timedSectionType,
    presentTypes,
    answers,
    sortedSections,
    timeoutDialog,
    countdown: timeoutCountdown,
    peekNext: peekTimeoutNext,
    reportSectionExpired,
    clearTimeoutDialog,
    flushBeforeNavigate,
    sealSection,
    enterSection,
    goToSection: nav.goToSection,
    onExhausted: onTimeoutExhausted,
  })

  const onContinue = useCallback(() => {
    void handleTimeoutContinue()
  }, [handleTimeoutContinue])

  return (
    <>
      <ExamHeader
        title={test.title}
        isPreview={isPreview}
        isPractice={isPractice}
        presentTypes={presentTypes}
        currentType={nav.currentType}
        sectionStates={isPreview ? undefined : sectionStates}
        unlockableType={isPreview ? null : unlockableType}
        onSwitchType={onSwitchType}
        showAiPaced={showAiPaced}
        showCountdown={showCountdown}
        remainingSec={remainingSec}
        totalAnswered={totalAnswered}
        totalQuestions={totalQuestions}
        showFinishSection={!isPreview && !isPractice}
        onFinishSection={onFinishSection}
        finishDisabled={finishDisabled}
        onSubmit={submitTest}
        isSubmitting={isSubmitting}
      />
      <TimeoutDialog
        info={timeoutDialog}
        countdown={timeoutCountdown}
        onContinue={onContinue}
      />
    </>
  )
}
