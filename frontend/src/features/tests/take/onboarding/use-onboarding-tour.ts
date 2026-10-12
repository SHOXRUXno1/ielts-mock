import { useCallback, useEffect, useState } from 'react'
import type { SectionType } from '../../data/schema'
import { TOUR_VERSION } from './tour-steps'

/**
 * Per-section onboarding state.
 *
 * The "seen" flag is persisted in ``localStorage`` so a student is not
 * re-greeted every time they revisit a section. The flag is keyed with a
 * version suffix (``tour:v<N>:<section>``) — bumping ``TOUR_VERSION`` in
 * ``tour-steps.ts`` invalidates all old flags and re-shows the refreshed
 * tour once.
 *
 * All reads/writes are wrapped in try/catch because ``localStorage`` can
 * throw (Safari private mode, blocked site data, sandboxed iframes). On
 * failure the hook defaults to "show the tour" rather than "hide it",
 * which errs on the side of helpful.
 */

const PREFIX = `tour:v${TOUR_VERSION}:`

function storageKey(section: SectionType): string {
  return `${PREFIX}${section}`
}

function hasSeen(section: SectionType): boolean {
  try {
    return localStorage.getItem(storageKey(section)) === '1'
  } catch {
    return false
  }
}

function markSeen(section: SectionType): void {
  try {
    localStorage.setItem(storageKey(section), '1')
  } catch {
    // Ignored — a one-time re-greet next session is harmless.
  }
}

function clearSeen(section: SectionType): void {
  try {
    localStorage.removeItem(storageKey(section))
  } catch {
    // Ignored.
  }
}

type UseOnboardingTourResult = {
  /** True while the tour overlay should be visible. */
  isOpen: boolean
  /** Called by the user's Help ("?") button to re-run the tour. */
  openTour: () => void
  /** Close + persist as seen. */
  closeTour: () => void
  /** For tests / developer tools. */
  resetSeen: () => void
}

/**
 * Opens the tour automatically the first time a student lands in
 * ``section`` and never again (per device) until ``openTour`` is
 * invoked by the Help button.
 *
 * Pass ``enabled: false`` to defer the first-time check (e.g. while the
 * attempt is still loading or on preview pages that should not greet a
 * first-time student).
 */
export function useOnboardingTour(
  section: SectionType | null,
  { enabled = true }: { enabled?: boolean } = {},
): UseOnboardingTourResult {
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    if (!enabled || !section) return
    // Short tick before showing: lets the section mount its DOM first,
    // otherwise react-joyride targets like [data-tour="…"] are missing
    // and the first step falls back to body.
    if (hasSeen(section)) return
    const timer = window.setTimeout(() => setIsOpen(true), 400)
    return () => window.clearTimeout(timer)
  }, [section, enabled])

  const openTour = useCallback(() => {
    if (!section) return
    // Replaying from the Help button: don't delete the "seen" flag — we
    // just open now, and the next auto-open on first visit still works
    // for the student's other devices.
    setIsOpen(true)
  }, [section])

  const closeTour = useCallback(() => {
    if (section) markSeen(section)
    setIsOpen(false)
  }, [section])

  const resetSeen = useCallback(() => {
    if (section) clearSeen(section)
  }, [section])

  return { isOpen, openTour, closeTour, resetSeen }
}
