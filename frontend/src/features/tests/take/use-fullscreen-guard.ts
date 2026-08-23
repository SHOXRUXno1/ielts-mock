import { useCallback, useEffect, useRef, useState } from 'react'
import { reportIntegrityEvent } from '@/lib/api/attempts'
import {
  consumeIntentionalExit,
  enterExamFullscreen,
  isExamFullscreen,
} from './exam-fullscreen'

/** Seconds a student has to re-enter fullscreen before the attempt is closed. */
export const FULLSCREEN_GRACE_SECONDS = 3

/**
 * Change events fire during transitions between elements (documentElement →
 * <video>, both directions). Waiting a beat before deciding stops the
 * intermediate state from being read as a violation.
 */
const DEBOUNCE_MS = 500

type Options = {
  attemptId: string | null | undefined
  /** Preview means an admin is inspecting the test — no violations should apply. */
  isPreview: boolean
  onTerminated: () => void
}

/**
 * Watches for the student leaving fullscreen mid-exam. On a real exit, opens
 * an overlay with a 10-second countdown and a Return button; if the student
 * comes back inside the window, the overlay closes and the exam continues; if
 * the window expires, the server closes the attempt and the caller is asked
 * to navigate away.
 *
 * The guard is intentionally lax: fullscreenchange also fires when the
 * examiner video enters its own fullscreen, when we exit at the end of the
 * exam, and (in some browsers) briefly while switching between elements.
 * Those cases must not cost the student a strike, so the guard requires
 * *both* "not intentional" and "no fullscreen element after the debounce".
 */
export function useFullscreenGuard({
  attemptId,
  isPreview,
  onTerminated,
}: Options) {
  const [violated, setViolated] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(FULLSCREEN_GRACE_SECONDS)

  // Refs so the effect below can react to the latest values without
  // re-subscribing to fullscreenchange on every render.
  const violatedRef = useRef(false)
  const attemptIdRef = useRef(attemptId)
  const onTerminatedRef = useRef(onTerminated)
  const terminatingRef = useRef(false)

  // Sync the refs in effects (writing during render trips the react-compiler
  // "cannot access refs during render" rule).
  useEffect(() => {
    attemptIdRef.current = attemptId
  }, [attemptId])
  useEffect(() => {
    onTerminatedRef.current = onTerminated
  }, [onTerminated])

  const clearViolation = useCallback(() => {
    violatedRef.current = false
    setViolated(false)
    setSecondsLeft(FULLSCREEN_GRACE_SECONDS)
  }, [])

  const returnToFullscreen = useCallback(() => {
    enterExamFullscreen()
    // The fullscreenchange listener will call clearViolation once it sees the
    // page back in fullscreen; doing it here as well would race that listener.
  }, [])

  useEffect(() => {
    if (isPreview) return
    if (!attemptId) return

    let debounceTimer: ReturnType<typeof setTimeout> | null = null

    const onChange = () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        debounceTimer = null

        // Intentional exits (finish, submit, forced termination) must be
        // consumed even if we are still in fullscreen, so a stale flag cannot
        // silence a later real violation.
        const intentional = consumeIntentionalExit()

        if (isExamFullscreen()) {
          if (violatedRef.current) clearViolation()
          return
        }

        if (intentional) return
        if (violatedRef.current) return

        violatedRef.current = true
        setViolated(true)
        setSecondsLeft(FULLSCREEN_GRACE_SECONDS)

        const id = attemptIdRef.current
        if (id) {
          void reportIntegrityEvent(id, 'fullscreen_exit', false).catch(() => {
            // The countdown still runs even if the log write fails; the
            // terminal call is what actually closes the attempt.
          })
        }
      }, DEBOUNCE_MS)
    }

    document.addEventListener('fullscreenchange', onChange)
    document.addEventListener('webkitfullscreenchange', onChange)
    return () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      document.removeEventListener('fullscreenchange', onChange)
      document.removeEventListener('webkitfullscreenchange', onChange)
    }
  }, [attemptId, isPreview, clearViolation])

  // Countdown ticks. Only runs while a violation is open.
  useEffect(() => {
    if (!violated) return
    const interval = setInterval(() => {
      setSecondsLeft((s) => (s > 0 ? s - 1 : 0))
    }, 1000)
    return () => clearInterval(interval)
  }, [violated])

  // Ran out of time: ask the server to close the attempt, then navigate.
  useEffect(() => {
    if (!violated || secondsLeft > 0) return
    if (terminatingRef.current) return
    const id = attemptIdRef.current
    if (!id) return
    terminatingRef.current = true
    void reportIntegrityEvent(id, 'fullscreen_exit', true)
      .catch(() => {
        // Even if the terminal call fails, redirect: the recorded event and
        // the (likely) network issue are the admin's problem, not the
        // student's to keep sitting through.
      })
      .finally(() => {
        onTerminatedRef.current()
      })
  }, [violated, secondsLeft])

  return {
    violated,
    secondsLeft,
    returnToFullscreen,
  }
}
