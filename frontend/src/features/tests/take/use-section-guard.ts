import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import type { SectionType } from '../data/schema'
import { collectAnswersForTypes } from './collect-answers'
import { SECTION_LABELS } from './constants'
import { isBenignSectionConflict } from './section-conflict'
import { resolveSealedRedirectTarget } from './section-guard-logic'
import { isNextSection, nextUnlockableType } from './section-order'
import { useTakeTest } from './take-test-context'
import { useTestNavigation } from './use-test-navigation'

type PendingSwitch = {
  from: SectionType
  to: SectionType
  /** True when the URL already changed to `to` (deep-link). Cancel must bounce back. */
  urlMoved: boolean
}

/**
 * URL-driven section guards for sealed / not_started transitions.
 * Preview mode is a no-op.
 *
 * Exam order is sequential: you cannot skip Listening → Writing.
 */
export function useSectionGuard() {
  const ctx = useTakeTest()
  const nav = useTestNavigation()
  const [pendingSwitch, setPendingSwitch] = useState<PendingSwitch | null>(null)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const handledKeyRef = useRef<string | null>(null)
  const toastKeyRef = useRef<string | null>(null)
  const cancelInFlightRef = useRef(false)
  const switchInFlightRef = useRef(false)

  const {
    isPreview,
    isPractice,
    attemptId,
    presentTypes,
    sealedTypes,
    activeSectionType,
    allSealed,
    stateOf,
    enterSection,
    sealSection,
    flushBeforeNavigate,
    finished,
    answers,
    sortedSections,
    setShowSubmitDialog,
    inputsLocked,
  } = ctx

  const triggerSubmit = useCallback(() => {
    setShowSubmitDialog(true)
  }, [setShowSubmitDialog])

  useEffect(() => {
    if (isPreview || !attemptId || finished || ctx.isReviewRoute) return
    if (allSealed) {
      triggerSubmit()
    }
  }, [isPreview, attemptId, finished, allSealed, triggerSubmit, ctx.isReviewRoute])

  // Drop stale confirm if Finish/timeout already advanced progress.
  useEffect(() => {
    if (!pendingSwitch) return
    const toState = stateOf(pendingSwitch.to)
    if (toState === 'active' || activeSectionType === pendingSwitch.to) {
      setConfirmOpen(false)
      setPendingSwitch(null)
      handledKeyRef.current = null
    }
  }, [pendingSwitch, stateOf, activeSectionType])

  // After Cancel: clear handledKey only once URL is back on `from`.
  const cancelReturnTypeRef = useRef<SectionType | null>(null)
  useEffect(() => {
    const expected = cancelReturnTypeRef.current
    if (!expected) return
    if (nav.currentType === expected) {
      handledKeyRef.current = null
      cancelReturnTypeRef.current = null
      cancelInFlightRef.current = false
    }
  }, [nav.currentType])

  useEffect(() => {
    if (isPreview || !attemptId || finished) return
    if (ctx.isReviewRoute) return
    // Practice mode: only one section exists; the /practice URL never crosses
    // sections, so the sequential guard has nothing to enforce.
    if (isPractice) return
    if (switchInFlightRef.current) return
    // Time's up owns the handoff — entering now would start the next timer.
    if (inputsLocked) return

    const type = nav.currentType
    const state = stateOf(type)
    if (!state) return

    const key = `${attemptId}:${type}:${state}:${activeSectionType ?? 'none'}`
    if (handledKeyRef.current === key) return

    if (state === 'sealed') {
      const target = resolveSealedRedirectTarget({
        hold: inputsLocked,
        sealedTypes,
        activeType: activeSectionType,
        presentTypes,
        current: type,
      })
      if (target === null) return
      handledKeyRef.current = key
      const toastKey = `sealed:${type}`
      if (toastKeyRef.current !== toastKey) {
        toastKeyRef.current = toastKey
        toast.info(
          `${SECTION_LABELS[type]} section is already completed`,
        )
      }
      if (target === 'review') {
        triggerSubmit()
      } else {
        void nav.goToSection(target)
      }
      return
    }

    if (state === 'active') {
      handledKeyRef.current = key
      return
    }

    // not_started — only the next section in order may be opened
    const unlockable = nextUnlockableType(
      presentTypes,
      stateOf,
      activeSectionType,
    )

    if (!activeSectionType) {
      handledKeyRef.current = key
      const first = unlockable
      if (!first) return
      if (type !== first) {
        void nav.goToSection(first)
        return
      }
      // Speaking has a readiness gate; leave state as not_started and let the
      // gate call enterSection when the student clicks Start.
      if (first === 'speaking') return
      void enterSection(first).catch(() => {
        toast.error(`Failed to start ${SECTION_LABELS[first]}`)
      })
      return
    }

    if (activeSectionType === type) {
      handledKeyRef.current = key
      return
    }

    // Deep-link / tab skip ahead (e.g. Listening → Writing) — bounce back
    if (!isNextSection(activeSectionType, type, presentTypes)) {
      handledKeyRef.current = key
      const next = unlockable
      toast.info(
        next
          ? `Sections must be taken in order. Continue with ${SECTION_LABELS[next]} next.`
          : 'Sections must be taken in order.',
      )
      void nav.goToSection(activeSectionType)
      return
    }

    // Immediate next section while another is active → confirm
    handledKeyRef.current = key
    const from = activeSectionType
    const to = type
    queueMicrotask(() => {
      setPendingSwitch({ from, to, urlMoved: true })
      setConfirmOpen(true)
    })
  }, [
    isPreview,
    isPractice,
    attemptId,
    finished,
    ctx.isReviewRoute,
    nav.currentType,
    stateOf,
    activeSectionType,
    presentTypes,
    sealedTypes,
    enterSection,
    nav,
    triggerSubmit,
    inputsLocked,
  ])

  const confirmSwitch = useCallback(async () => {
    if (!pendingSwitch) return
    const { from, to } = pendingSwitch
    if (!isNextSection(from, to, presentTypes)) {
      setPendingSwitch(null)
      setConfirmOpen(false)
      toast.info('Sections must be taken in order.')
      await nav.goToSection(from)
      return
    }
    // Clear pending before closing so AlertDialog onOpenChange → cancel is a no-op.
    setPendingSwitch(null)
    setConfirmOpen(false)
    switchInFlightRef.current = true
    try {
      await flushBeforeNavigate()
      const fromAnswers = collectAnswersForTypes(answers, sortedSections, [
        from,
      ])
      try {
        await sealSection({
          sectionType: from,
          answers: fromAnswers,
          reason: 'manual',
        })
      } catch (err) {
        if (!isBenignSectionConflict(err)) throw err
      }
      // Speaking has its own readiness gate — hold on the URL without
      // entering so the 20-min cap starts on the Start click there.
      if (to !== 'speaking') {
        await enterSection(to)
      }
      handledKeyRef.current = null
      await nav.goToSection(to)
    } catch {
      handledKeyRef.current = null
      toast.error('Failed to switch section')
      await nav.goToSection(from)
    } finally {
      switchInFlightRef.current = false
    }
  }, [
    pendingSwitch,
    flushBeforeNavigate,
    sealSection,
    enterSection,
    nav,
    presentTypes,
    answers,
    sortedSections,
  ])

  const cancelSwitch = useCallback(async () => {
    if (cancelInFlightRef.current) {
      setConfirmOpen(false)
      return
    }
    const pending = pendingSwitch
    if (!pending) {
      setConfirmOpen(false)
      return
    }
    cancelInFlightRef.current = true
    setConfirmOpen(false)
    setPendingSwitch(null)
    // Keep handledKeyRef on the dismissed `to` URL until we land on `from`
    // (see cancelReturnTypeRef effect) so the modal cannot reopen mid-navigate.
    if (!pending.urlMoved) {
      cancelInFlightRef.current = false
      return
    }
    cancelReturnTypeRef.current = pending.from
    try {
      await nav.goToSection(pending.from)
    } catch {
      // Stay blocked on `to` until a later navigation succeeds.
      cancelInFlightRef.current = false
    }
  }, [pendingSwitch, nav])

  /** Open the switch confirm without changing the URL first (header tabs). */
  const requestSwitch = useCallback(
    (to: SectionType) => {
      if (isPreview || isPractice) {
        void nav.goToSection(to)
        return
      }
      if (to === nav.currentType) return
      if (switchInFlightRef.current) return

      const toState = stateOf(to)
      if (toState === 'sealed') {
        toast.info(`${SECTION_LABELS[to]} section is already completed`)
        return
      }
      if (toState === 'active' || activeSectionType === to) {
        void nav.goToSection(to)
        return
      }

      const unlockable = nextUnlockableType(
        presentTypes,
        stateOf,
        activeSectionType,
      )
      if (to !== unlockable) {
        toast.info(
          unlockable
            ? `Sections must be taken in order. Continue with ${SECTION_LABELS[unlockable]} next.`
            : 'Sections must be taken in order.',
        )
        return
      }

      if (!activeSectionType) {
        void enterSection(to)
          .then(() => nav.goToSection(to))
          .catch(() => {
            toast.error(`Failed to start ${SECTION_LABELS[to]}`)
          })
        return
      }

      setPendingSwitch({ from: activeSectionType, to, urlMoved: false })
      setConfirmOpen(true)
    },
    [
      isPreview,
      isPractice,
      nav,
      stateOf,
      activeSectionType,
      presentTypes,
      enterSection,
    ],
  )

  return {
    confirmOpen,
    pendingSwitch,
    confirmSwitch,
    cancelSwitch,
    requestSwitch,
    triggerSubmit,
  }
}
