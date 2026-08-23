import { useCallback, useEffect, useRef, useState } from 'react'
import { reportIntegrityEvent } from '@/lib/api/attempts'
import {
  consumeIntentionalExit,
  enterExamFullscreen,
  isExamFullscreen,
  isExamFullscreenSupported,
} from './exam-fullscreen'

/**
 * How the exam came to be outside fullscreen. The two cases carry very
 * different weight, so the guard never conflates them.
 *
 * - `exit`: a fullscreenchange arrived while the page was live. The student
 *   did this on purpose, so the countdown runs and the attempt is closed if
 *   they do not come back.
 * - `reload`: the page loaded already outside fullscreen — F5, a restored
 *   tab, or reopening the browser after the machine died. No browser can
 *   restore fullscreen without a user gesture, so this state says nothing
 *   about intent and must not cost the student their exam. The exam is
 *   blocked until they re-enter, and the event is logged for the admin.
 */
export type FullscreenViolationKind = 'exit' | 'reload'

/** Seconds a student has to re-enter fullscreen before the attempt is closed. */
export const FULLSCREEN_GRACE_SECONDS = 3

/**
 * Change events fire during transitions between elements (documentElement →
 * <video>, both directions). Waiting a beat before deciding stops the
 * intermediate state from being read as a violation.
 */
const DEBOUNCE_MS = 500

/**
 * The guard must also check the state it *starts* in, not only changes to it.
 * Reloading the page drops fullscreen and resumes the exam through the
 * ?resume route, which skips the intro screen — so no fullscreenchange ever
 * arrives and F5 would otherwise be a free way out.
 *
 * The window is longer than the debounce because the requestFullscreen fired
 * by the intro screen's Start click can still be in flight when the exam
 * chrome mounts, and a legitimate start must not be flagged.
 */
const INITIAL_CHECK_MS = 1500

const EVENT_NAME: Record<FullscreenViolationKind, 'fullscreen_exit' | 'fullscreen_reload'> = {
  exit: 'fullscreen_exit',
  reload: 'fullscreen_reload',
}

type Options = {
  attemptId: string | null | undefined
  /** Preview means an admin is inspecting the test — no violations should apply. */
  isPreview: boolean
  onTerminated: () => void
}

/**
 * Keeps the student inside fullscreen for the duration of the exam.
 *
 * Whenever the exam is found running outside fullscreen an opaque overlay
 * takes over the screen, so leaving fullscreen never becomes a way to read
 * the questions in a windowed tab. What differs is the consequence: a
 * deliberate exit runs a countdown and ends the attempt, while a page that
 * merely loaded outside fullscreen only has to be brought back.
 *
 * The guard is deliberately lax about what counts as an exit: fullscreenchange
 * also fires when the examiner video takes over fullscreen, when we leave at
 * the end of the exam, and briefly while switching between elements. Those
 * must not cost a strike, so a violation needs *both* "not intentional" and
 * "no fullscreen element once things settle".
 */
export function useFullscreenGuard({
  attemptId,
  isPreview,
  onTerminated,
}: Options) {
  const [violation, setViolation] = useState<FullscreenViolationKind | null>(
    null,
  )
  const [secondsLeft, setSecondsLeft] = useState(FULLSCREEN_GRACE_SECONDS)

  // Refs so the effect below can react to the latest values without
  // re-subscribing to fullscreenchange on every render.
  const violationRef = useRef<FullscreenViolationKind | null>(null)
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
    violationRef.current = null
    setViolation(null)
    setSecondsLeft(FULLSCREEN_GRACE_SECONDS)
  }, [])

  const returnToFullscreen = useCallback(() => {
    enterExamFullscreen()
    // The fullscreenchange listener will clear the violation once it sees the
    // page back in fullscreen; doing it here as well would race that listener.
  }, [])

  useEffect(() => {
    if (isPreview) return
    if (!attemptId) return
    // Where the page cannot go fullscreen at all, there is no rule to break.
    if (!isExamFullscreenSupported()) return

    let timer: ReturnType<typeof setTimeout> | null = null

    const evaluate = (kind: FullscreenViolationKind) => {
      // Intentional exits (finish, submit, forced termination) must be
      // consumed even if we are still in fullscreen, so a stale flag cannot
      // silence a later real violation.
      const intentional = consumeIntentionalExit()

      if (isExamFullscreen()) {
        if (violationRef.current) clearViolation()
        return
      }

      if (intentional) return
      // An open violation is never upgraded: a `reload` block must not turn
      // into a terminating countdown because some later event fired.
      if (violationRef.current) return

      violationRef.current = kind
      setViolation(kind)
      setSecondsLeft(FULLSCREEN_GRACE_SECONDS)

      const id = attemptIdRef.current
      if (id) {
        void reportIntegrityEvent(id, EVENT_NAME[kind], false).catch(() => {
          // The block still stands even if the log write fails; the terminal
          // call is what actually closes the attempt.
        })
      }
    }

    // One timer slot for both triggers: a change arriving during the initial
    // window simply reschedules the same check, so the two cannot race.
    const schedule = (delay: number, kind: FullscreenViolationKind) => {
      if (timer) clearTimeout(timer)
      timer = setTimeout(() => {
        timer = null
        evaluate(kind)
      }, delay)
    }

    schedule(INITIAL_CHECK_MS, 'reload')
    const onChange = () => schedule(DEBOUNCE_MS, 'exit')

    document.addEventListener('fullscreenchange', onChange)
    document.addEventListener('webkitfullscreenchange', onChange)
    return () => {
      if (timer) clearTimeout(timer)
      document.removeEventListener('fullscreenchange', onChange)
      document.removeEventListener('webkitfullscreenchange', onChange)
    }
  }, [attemptId, isPreview, clearViolation])

  // Countdown ticks. Only a deliberate exit is on the clock.
  useEffect(() => {
    if (violation !== 'exit') return
    const interval = setInterval(() => {
      setSecondsLeft((s) => (s > 0 ? s - 1 : 0))
    }, 1000)
    return () => clearInterval(interval)
  }, [violation])

  // Ran out of time: ask the server to close the attempt, then navigate.
  useEffect(() => {
    if (violation !== 'exit' || secondsLeft > 0) return
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
  }, [violation, secondsLeft])

  return {
    violation,
    secondsLeft,
    returnToFullscreen,
  }
}
