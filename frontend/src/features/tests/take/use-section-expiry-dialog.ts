import { useCallback, useEffect, useRef, useState } from 'react'
import type { SectionType } from '../data/schema'

export const TIMEOUT_AUTO_CONTINUE_SEC = 5

export type TimeoutDialogInfo = {
  from: SectionType
  next: SectionType | null
}

/**
 * Owns the Time's up dialog, input lock, and auto-continue countdown.
 * First report for a section opens the modal; later reports only refresh `next`.
 */
export function useSectionExpiryDialog(
  onFirstOpen: () => void | Promise<unknown>,
) {
  const [timeoutDialog, setTimeoutDialog] = useState<TimeoutDialogInfo | null>(
    null,
  )
  const [inputsLocked, setInputsLocked] = useState(false)
  const [countdown, setCountdown] = useState<number | null>(null)
  const handledRef = useRef<SectionType | null>(null)
  const nextRef = useRef<SectionType | null>(null)

  const reportSectionExpired = useCallback(
    (info: TimeoutDialogInfo) => {
      nextRef.current = info.next
      if (handledRef.current === info.from) {
        setTimeoutDialog((prev) =>
          prev && prev.from === info.from && prev.next !== info.next
            ? { ...prev, next: info.next }
            : prev,
        )
        return
      }
      handledRef.current = info.from
      setInputsLocked(true)
      setTimeoutDialog(info)
      setCountdown(TIMEOUT_AUTO_CONTINUE_SEC)
      void onFirstOpen()
    },
    [onFirstOpen],
  )

  const clearTimeoutDialog = useCallback(() => {
    setTimeoutDialog(null)
    setInputsLocked(false)
    setCountdown(null)
    handledRef.current = null
    nextRef.current = null
  }, [])

  useEffect(() => {
    if (countdown == null || countdown <= 0) return
    const id = window.setTimeout(() => {
      setCountdown((prev) => (prev == null || prev <= 0 ? prev : prev - 1))
    }, 1000)
    return () => window.clearTimeout(id)
  }, [countdown])

  const peekTimeoutNext = useCallback(() => nextRef.current, [])
  const isExpiryHandled = useCallback(() => handledRef.current != null, [])

  return {
    timeoutDialog,
    countdown,
    inputsLocked,
    reportSectionExpired,
    clearTimeoutDialog,
    peekTimeoutNext,
    isExpiryHandled,
  }
}
