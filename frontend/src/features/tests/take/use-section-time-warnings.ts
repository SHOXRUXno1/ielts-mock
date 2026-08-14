import { useEffect, useRef } from 'react'
import { toast } from 'sonner'
import type { SectionType } from '../data/schema'

/** Fire 5-minute / 1-minute toasts once per section when the clock crosses each threshold. */
export function useSectionTimeWarnings({
  remainingMs,
  sectionType,
  enabled,
  suppressFiveMin,
}: {
  remainingMs: number | null
  sectionType: SectionType
  enabled: boolean
  suppressFiveMin: boolean
}) {
  const seenRef = useRef<Set<string>>(new Set())
  const prevSecRef = useRef<number | null>(null)

  useEffect(() => {
    seenRef.current = new Set()
    prevSecRef.current = null
  }, [sectionType])

  useEffect(() => {
    if (!enabled || sectionType === 'speaking') {
      prevSecRef.current = null
      return
    }
    if (remainingMs == null || remainingMs <= 0) return
    const seconds = Math.floor(remainingMs / 1000)
    const prev = prevSecRef.current
    prevSecRef.current = seconds
    if (prev == null) return

    const fiveKey = `${sectionType}:5`
    const oneKey = `${sectionType}:1`
    if (
      !suppressFiveMin &&
      prev > 300 &&
      seconds <= 300 &&
      !seenRef.current.has(fiveKey)
    ) {
      seenRef.current.add(fiveKey)
      toast.info('5 minutes remaining in this section', { duration: 5000 })
    }
    if (prev > 60 && seconds <= 60 && !seenRef.current.has(oneKey)) {
      seenRef.current.add(oneKey)
      toast.warning('1 minute remaining', { duration: 5000 })
    }
  }, [remainingMs, sectionType, enabled, suppressFiveMin])
}
