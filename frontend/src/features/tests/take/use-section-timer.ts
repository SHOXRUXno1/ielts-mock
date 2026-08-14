import { useEffect, useState } from 'react'

type Options = {
  /** ISO ends_at from the active SectionProgress row */
  endsAt: string | null | undefined
  /**
   * Clock skew as serverNow - clientNow (from skewFromServerNow).
   * Server time ≈ Date.now() + skewMs.
   */
  skewMs: number
  enabled: boolean
}

/**
 * Per-section countdown driven by server ends_at + clock skew.
 * Date.now() alone is never the source of truth for remaining time.
 * `expired` flips in the same tick as the display hitting 00:00.
 * Server-side grace still accepts a last flush after lock; the UI must not wait.
 */
export function useSectionTimer({
  endsAt,
  skewMs,
  enabled,
}: Options) {
  const [nowOnServer, setNowOnServer] = useState(() => Date.now() + skewMs)

  useEffect(() => {
    if (!enabled || !endsAt) return
    const tick = () => setNowOnServer(Date.now() + skewMs)
    // Sample in a macrotask so we don't sync-setState inside the effect body.
    const kick = window.setTimeout(tick, 0)
    // 2Hz — smooth enough for mm:ss without burning a full rAF loop.
    const id = window.setInterval(tick, 500)
    return () => {
      window.clearTimeout(kick)
      window.clearInterval(id)
    }
  }, [enabled, endsAt, skewMs])

  const endsAtMs = endsAt ? Date.parse(endsAt) : NaN
  const hasDeadline = enabled && Number.isFinite(endsAtMs)
  const remainingMs = hasDeadline ? Math.max(0, endsAtMs - nowOnServer) : null
  const remainingSec =
    remainingMs == null ? 0 : Math.ceil(remainingMs / 1000)
  const expired = hasDeadline && remainingMs === 0

  return {
    remainingMs,
    remainingSec,
    expired,
    nowOnServer,
  }
}
