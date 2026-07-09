import { createRef } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { renderHook } from 'vitest-browser-react'
import { useTranscriptAutoscroll } from './use-transcript-autoscroll'

function createScrollElement(scrollHeight: number, clientHeight: number) {
  let scrollTop = 0
  const el = document.createElement('div')
  Object.defineProperty(el, 'scrollHeight', {
    configurable: true,
    get() {
      return scrollHeight
    },
  })
  Object.defineProperty(el, 'clientHeight', {
    configurable: true,
    get() {
      return clientHeight
    },
  })
  Object.defineProperty(el, 'scrollTop', {
    configurable: true,
    get() {
      return scrollTop
    },
    set(value: number) {
      scrollTop = value
    },
  })
  return {
    el,
    getScrollTop: () => scrollTop,
    setScrollTop: (value: number) => {
      scrollTop = value
    },
  }
}

describe('useTranscriptAutoscroll', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('scrolls instantly when history grows and user is at bottom', async () => {
    const scrollRef = createRef<HTMLDivElement>()
    const { el, getScrollTop } = createScrollElement(500, 200)
    scrollRef.current = el

    const { rerender } = await renderHook(
      ({ length = 1 }: { length?: number } = {}) =>
        useTranscriptAutoscroll(scrollRef, length, true),
      { initialProps: { length: 1 } },
    )

    await vi.waitFor(() => expect(getScrollTop()).toBe(500))

    await rerender({ length: 2 })
    await vi.waitFor(() => expect(getScrollTop()).toBe(500))
  })

  it('does not auto-scroll when user pinned away from bottom', async () => {
    const scrollRef = createRef<HTMLDivElement>()
    const { el, getScrollTop, setScrollTop } = createScrollElement(500, 200)
    scrollRef.current = el

    const { result, rerender, act } = await renderHook(
      ({ length = 1 }: { length?: number } = {}) =>
        useTranscriptAutoscroll(scrollRef, length, true),
      { initialProps: { length: 1 } },
    )

    await vi.waitFor(() => expect(getScrollTop()).toBe(500))

    setScrollTop(50)
    await act(async () => {
      result.current.onScroll()
    })
    await vi.waitFor(() => expect(result.current.showJumpToLatest).toBe(true))

    await rerender({ length: 2 })
    expect(getScrollTop()).toBe(50)

    await act(async () => {
      result.current.jumpToLatest()
    })
    expect(getScrollTop()).toBe(500)
    await vi.waitFor(() => expect(result.current.showJumpToLatest).toBe(false))
  })
})
