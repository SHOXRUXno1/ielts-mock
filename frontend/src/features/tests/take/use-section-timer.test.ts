import { describe, expect, it, vi } from 'vitest'
import { renderHook } from 'vitest-browser-react'
import { skewFromServerNow } from './clock-skew'
import { useSectionTimer } from './use-section-timer'

describe('skewFromServerNow', () => {
  it('returns server - client delta', () => {
    const now = Date.now()
    vi.spyOn(Date, 'now').mockReturnValue(now)
    const server = new Date(now + 1500).toISOString()
    expect(skewFromServerNow(server)).toBe(1500)
    vi.restoreAllMocks()
  })

  it('returns 0 for invalid input', () => {
    expect(skewFromServerNow(null)).toBe(0)
    expect(skewFromServerNow('not-a-date')).toBe(0)
  })
})

describe('useSectionTimer', () => {
  it('computes remaining from ends_at and keeps it after remount (F5)', async () => {
    const endsAt = new Date(Date.now() + 120_000).toISOString()

    const first = await renderHook(() =>
      useSectionTimer({ endsAt, skewMs: 0, enabled: true }),
    )
    const firstRemaining = first.result.current!.remainingSec
    expect(firstRemaining).toBeGreaterThan(110)
    expect(firstRemaining).toBeLessThanOrEqual(120)
    expect(first.result.current!.expired).toBe(false)
    first.unmount()

    const remounted = await renderHook(() =>
      useSectionTimer({ endsAt, skewMs: 0, enabled: true }),
    )
    expect(remounted.result.current!.remainingSec).toBeGreaterThan(105)
    expect(remounted.result.current!.remainingSec).toBeLessThanOrEqual(
      firstRemaining,
    )
    expect(remounted.result.current!.expired).toBe(false)
    remounted.unmount()
  })

  it('is expired as soon as ends_at is reached', async () => {
    const endsAt = new Date(Date.now() - 250).toISOString()
    const hook = await renderHook(() =>
      useSectionTimer({ endsAt, skewMs: 0, enabled: true }),
    )
    await vi.waitFor(() => {
      expect(hook.result.current).not.toBeNull()
      expect(hook.result.current!.remainingSec).toBe(0)
      expect(hook.result.current!.expired).toBe(true)
    })
    hook.unmount()
  })

})
