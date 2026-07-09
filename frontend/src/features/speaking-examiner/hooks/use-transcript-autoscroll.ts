import { useCallback, useEffect, useRef, useState, type RefObject } from 'react'

const BOTTOM_THRESHOLD_PX = 40

export function useTranscriptAutoscroll(
  scrollRef: RefObject<HTMLElement | null>,
  historyLength: number,
  enabled: boolean,
) {
  const userPinnedRef = useRef(false)
  const [showJumpToLatest, setShowJumpToLatest] = useState(false)

  const jumpToLatest = useCallback(() => {
    const el = scrollRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
    userPinnedRef.current = false
    setShowJumpToLatest(false)
  }, [scrollRef])

  const onScroll = useCallback(() => {
    const el = scrollRef.current
    if (!el) return
    const atBottom =
      el.scrollTop + el.clientHeight >= el.scrollHeight - BOTTOM_THRESHOLD_PX
    userPinnedRef.current = !atBottom
    setShowJumpToLatest(!atBottom)
  }, [scrollRef])

  useEffect(() => {
    if (!enabled || userPinnedRef.current) return
    const el = scrollRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
  }, [historyLength, enabled, scrollRef])

  return {
    onScroll,
    showJumpToLatest,
    jumpToLatest,
  }
}
