import { useCallback, useEffect, useRef, useState } from 'react'
import { canAutostartSpeaking, markSpeakingAutostartGesture } from '../lib/user-activation'
import type { Phase } from '../types/phase'

export type AutostartBlockedReason = 'mic' | 'activation' | 'failed'

type CheckMicrophone = (options?: { silent?: boolean }) => Promise<boolean>

type UseSpeakingAutostartOptions = {
  enabled: boolean
  phase: Phase
  isTokenPending: boolean
  score: unknown
  checkMicrophone: CheckMicrophone
  /** Resolves true when the examiner session started successfully. */
  handleStart: () => boolean | Promise<boolean>
}

export function useSpeakingAutostart({
  enabled,
  phase,
  isTokenPending,
  score,
  checkMicrophone,
  handleStart,
}: UseSpeakingAutostartOptions) {
  const [autoStartPending, setAutoStartPending] = useState(false)
  const [blockedReason, setBlockedReason] = useState<AutostartBlockedReason | null>(
    null,
  )

  // Consumed once for the lifetime of this mount — do NOT reset on End Test,
  // otherwise stopSession would immediately re-trigger autostart.
  const autoStartConsumedRef = useRef(false)
  const inFlightRef = useRef(false)
  const checkMicrophoneRef = useRef(checkMicrophone)
  const handleStartRef = useRef(handleStart)

  useEffect(() => {
    checkMicrophoneRef.current = checkMicrophone
  }, [checkMicrophone])

  useEffect(() => {
    handleStartRef.current = handleStart
  }, [handleStart])

  const attemptStart = useCallback(async () => {
    if (inFlightRef.current) return
    inFlightRef.current = true
    setBlockedReason(null)
    setAutoStartPending(true)

    try {
      if (!canAutostartSpeaking()) {
        setBlockedReason('activation')
        return
      }

      const micOk = await checkMicrophoneRef.current({ silent: true })
      if (!micOk) {
        setBlockedReason('mic')
        return
      }

      const started = await handleStartRef.current()
      if (!started) {
        setBlockedReason('failed')
      }
    } catch {
      setBlockedReason('failed')
    } finally {
      inFlightRef.current = false
      setAutoStartPending(false)
    }
  }, [])

  useEffect(() => {
    if (!enabled) return
    if (score) return
    if (isTokenPending) return
    if (phase !== 'idle') return
    if (autoStartConsumedRef.current) return

    // Mark consumed only when the deferred start actually runs. React Strict Mode
    // mounts → cleanup → remount; clearing the timer must allow the second mount
    // to schedule a fresh attempt (otherwise autostart is skipped forever).
    const timer = window.setTimeout(() => {
      if (autoStartConsumedRef.current) return
      autoStartConsumedRef.current = true
      void attemptStart()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [enabled, phase, isTokenPending, score, attemptStart])

  const retry = useCallback(() => {
    // Explicit user tap — always allow audio / mic for this gesture.
    markSpeakingAutostartGesture()
    void attemptStart()
  }, [attemptStart])

  // Hide stale blocked UI once the live session is running.
  const visibleBlockedReason =
    phase === 'idle' || phase === 'loading' ? blockedReason : null

  return {
    autoStartPending,
    blockedReason: visibleBlockedReason,
    retry,
  }
}
