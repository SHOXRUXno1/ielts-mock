import { useCallback, useEffect, useRef } from 'react'
import { markSpeakingAutostartGesture } from '@/features/speaking-examiner/lib/user-activation'
import type { SealReason, SealSectionResponse } from '@/lib/api/section-progress'
import type { Section, SectionType } from '../data/schema'
import { collectAnswersForTypes } from './collect-answers'
import { parseSectionExpired, toExpiredInfo } from './section-expired'
import { asSectionType, nextTypeAfter } from './section-order'
import type { SectionAnswers } from './take-test-context'
import type { TimeoutDialogInfo } from './use-section-expiry-dialog'

type Options = {
  enabled: boolean
  timerExpired: boolean
  /** Section that owns the current ends_at. Must match expiredType. */
  deadlineType: SectionType | null
  expiredType: SectionType
  presentTypes: SectionType[]
  answers: Record<string, SectionAnswers>
  sortedSections: Section[]
  timeoutDialog: TimeoutDialogInfo | null
  countdown: number | null
  peekNext: () => SectionType | null
  reportSectionExpired: (info: TimeoutDialogInfo) => void
  clearTimeoutDialog: () => void
  flushBeforeNavigate: () => Promise<boolean>
  sealSection: (args: {
    sectionType: string
    answers?: Array<{
      question_id: string
      response: Record<string, unknown>
    }>
    reason?: SealReason
  }) => Promise<SealSectionResponse>
  enterSection: (sectionType: string) => Promise<unknown>
  goToSection: (type: SectionType) => Promise<unknown>
  onExhausted: () => void
}

/**
 * When the clock hits 00:00: lock + show Time's up immediately, seal
 * in the background, then auto-advance when the dialog countdown reaches 0.
 */
export function useSectionTimeout({
  enabled,
  timerExpired,
  deadlineType,
  expiredType,
  presentTypes,
  answers,
  sortedSections,
  timeoutDialog,
  countdown,
  peekNext,
  reportSectionExpired,
  clearTimeoutDialog,
  flushBeforeNavigate: _flushBeforeNavigate,
  sealSection,
  enterSection,
  goToSection,
  onExhausted,
}: Options) {
  const sealingRef = useRef(false)
  const continueInFlightRef = useRef(false)
  const sealPromiseRef = useRef<Promise<void> | null>(null)

  useEffect(() => {
    sealingRef.current = false
    continueInFlightRef.current = false
  }, [expiredType])

  useEffect(() => {
    if (!enabled || !timerExpired) return
    // Do not seal Speaking with a leftover 00:00 from the previous section.
    if (!deadlineType || deadlineType !== expiredType) return
    if (timeoutDialog || sealingRef.current) return
    sealingRef.current = true

    const localNext = nextTypeAfter(presentTypes, expiredType)
    reportSectionExpired({ from: expiredType, next: localNext })

    sealPromiseRef.current = (async () => {
      try {
        const all = collectAnswersForTypes(answers, sortedSections, [
          expiredType,
        ])
        const result = await sealSection({
          sectionType: expiredType,
          answers: all,
          reason: 'timeout',
        })
        reportSectionExpired({
          from: expiredType,
          next: asSectionType(result.next_section) ?? localNext,
        })
      } catch (err) {
        const detail = parseSectionExpired(err)
        if (detail) {
          const info = toExpiredInfo(detail, expiredType)
          reportSectionExpired({
            from: info.from ?? expiredType,
            next: info.next,
          })
          return
        }
        reportSectionExpired({ from: expiredType, next: localNext })
      }
    })()
  }, [
    enabled,
    timerExpired,
    deadlineType,
    timeoutDialog,
    expiredType,
    presentTypes,
    answers,
    sortedSections,
    reportSectionExpired,
    sealSection,
  ])

  const handleContinue = useCallback(async () => {
    if (continueInFlightRef.current || !timeoutDialog) return
    continueInFlightRef.current = true
    if (sealPromiseRef.current) {
      try {
        await sealPromiseRef.current
      } catch {
        /* already reflected on the dialog */
      }
      sealPromiseRef.current = null
    }
    const next = peekNext() ?? timeoutDialog.next
    sealingRef.current = false
    if (next) {
      if (next === 'speaking') markSpeakingAutostartGesture()
      try {
        await enterSection(next)
      } catch {
        /* may already be entered */
      }
      clearTimeoutDialog()
      await goToSection(next)
      return
    }
    clearTimeoutDialog()
    onExhausted()
  }, [
    timeoutDialog,
    peekNext,
    clearTimeoutDialog,
    enterSection,
    goToSection,
    onExhausted,
  ])

  useEffect(() => {
    if (countdown !== 0 || !timeoutDialog) return
    void handleContinue()
  }, [countdown, timeoutDialog, handleContinue])

  return { handleContinue }
}
