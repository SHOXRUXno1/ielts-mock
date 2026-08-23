import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { renderHook } from 'vitest-browser-react'
import { markIntentionalExamFullscreenExit } from './exam-fullscreen'
import {
  FULLSCREEN_GRACE_SECONDS,
  useFullscreenGuard,
} from './use-fullscreen-guard'

const reportIntegrityEventMock = vi.fn().mockResolvedValue({
  recorded: true,
  terminated: false,
  events_count: 1,
})

vi.mock('@/lib/api/attempts', () => ({
  reportIntegrityEvent: (...args: unknown[]) =>
    reportIntegrityEventMock(...args),
}))

function setFullscreenElement(el: Element | null) {
  Object.defineProperty(document, 'fullscreenElement', {
    configurable: true,
    get: () => el,
  })
}

function fireFullscreenChange() {
  document.dispatchEvent(new Event('fullscreenchange'))
}

beforeEach(() => {
  reportIntegrityEventMock.mockClear()
})

afterEach(() => {
  vi.restoreAllMocks()
  const doc = document as unknown as Record<string, unknown>
  delete doc.fullscreenElement
})

describe('useFullscreenGuard', () => {
  it('opens after the debounce when the student really left fullscreen', async () => {
    setFullscreenElement(document.documentElement)
    const { result } = await renderHook(() =>
      useFullscreenGuard({
        attemptId: 'attempt-1',
        isPreview: false,
        onTerminated: () => {},
      }),
    )

    expect(result.current.violated).toBe(false)

    setFullscreenElement(null)
    fireFullscreenChange()

    await vi.waitFor(() => expect(result.current.violated).toBe(true), {
      timeout: 1500,
    })
    expect(result.current.secondsLeft).toBe(FULLSCREEN_GRACE_SECONDS)
    expect(reportIntegrityEventMock).toHaveBeenCalledWith(
      'attempt-1',
      'fullscreen_exit',
      false,
    )
  })

  it('ignores a change that was flagged as intentional', async () => {
    setFullscreenElement(document.documentElement)
    const { result } = await renderHook(() =>
      useFullscreenGuard({
        attemptId: 'attempt-1',
        isPreview: false,
        onTerminated: () => {},
      }),
    )

    markIntentionalExamFullscreenExit()
    setFullscreenElement(null)
    fireFullscreenChange()

    await new Promise((r) => setTimeout(r, 800))

    expect(result.current.violated).toBe(false)
    expect(reportIntegrityEventMock).not.toHaveBeenCalled()
  })

  it('does not fire when the page still owns fullscreen on another element', async () => {
    setFullscreenElement(document.documentElement)
    const { result } = await renderHook(() =>
      useFullscreenGuard({
        attemptId: 'attempt-1',
        isPreview: false,
        onTerminated: () => {},
      }),
    )

    const video = document.createElement('video')
    setFullscreenElement(video)
    fireFullscreenChange()

    await new Promise((r) => setTimeout(r, 800))

    expect(result.current.violated).toBe(false)
    expect(reportIntegrityEventMock).not.toHaveBeenCalled()
  })

  it('clears the violation when fullscreen comes back before the countdown ends', async () => {
    setFullscreenElement(document.documentElement)
    const { result } = await renderHook(() =>
      useFullscreenGuard({
        attemptId: 'attempt-1',
        isPreview: false,
        onTerminated: () => {},
      }),
    )

    setFullscreenElement(null)
    fireFullscreenChange()
    await vi.waitFor(() => expect(result.current.violated).toBe(true), {
      timeout: 1500,
    })

    setFullscreenElement(document.documentElement)
    fireFullscreenChange()
    await vi.waitFor(() => expect(result.current.violated).toBe(false), {
      timeout: 1500,
    })
    expect(result.current.secondsLeft).toBe(FULLSCREEN_GRACE_SECONDS)
  })

  it('is a no-op in preview mode', async () => {
    setFullscreenElement(document.documentElement)
    const { result } = await renderHook(() =>
      useFullscreenGuard({
        attemptId: 'attempt-1',
        isPreview: true,
        onTerminated: () => {},
      }),
    )

    setFullscreenElement(null)
    fireFullscreenChange()

    await new Promise((r) => setTimeout(r, 800))

    expect(result.current.violated).toBe(false)
    expect(reportIntegrityEventMock).not.toHaveBeenCalled()
  })
})
