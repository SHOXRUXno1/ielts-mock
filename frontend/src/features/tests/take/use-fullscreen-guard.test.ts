import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { renderHook } from 'vitest-browser-react'
import {
  EXAM_FULLSCREEN_ENFORCED,
  markIntentionalExamFullscreenExit,
} from './exam-fullscreen'
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

/** Hide the Fullscreen API to emulate a browser that cannot go fullscreen. */
function removeFullscreenSupport() {
  for (const name of ['requestFullscreen', 'webkitRequestFullscreen']) {
    Object.defineProperty(document.documentElement, name, {
      configurable: true,
      writable: true,
      value: undefined,
    })
  }
}

function mount(overrides: { isPreview?: boolean; onTerminated?: () => void } = {}) {
  return renderHook(() =>
    useFullscreenGuard({
      attemptId: 'attempt-1',
      isPreview: overrides.isPreview ?? false,
      onTerminated: overrides.onTerminated ?? (() => {}),
    }),
  )
}

beforeEach(() => {
  reportIntegrityEventMock.mockClear()
})

afterEach(() => {
  vi.restoreAllMocks()
  const doc = document as unknown as Record<string, unknown>
  const el = document.documentElement as unknown as Record<string, unknown>
  delete doc.fullscreenElement
  delete el.requestFullscreen
  delete el.webkitRequestFullscreen
})

describe('useFullscreenGuard — while proctoring is switched off', () => {
  it('never opens a violation, whatever the page does', async () => {
    const onTerminated = vi.fn()
    setFullscreenElement(null)
    const { result } = await mount({ onTerminated })

    fireFullscreenChange()
    await new Promise((r) => setTimeout(r, (FULLSCREEN_GRACE_SECONDS + 2) * 1000))

    expect(result.current.violation).toBe(null)
    expect(onTerminated).not.toHaveBeenCalled()
    expect(reportIntegrityEventMock).not.toHaveBeenCalled()
  })
})

// The suites below describe the feature as it behaves when enforced. They run
// again by themselves the moment EXAM_FULLSCREEN_ENFORCED goes back to true.
describe.skipIf(!EXAM_FULLSCREEN_ENFORCED)('useFullscreenGuard — leaving fullscreen mid-exam', () => {
  it('opens after the debounce and reports a deliberate exit', async () => {
    setFullscreenElement(document.documentElement)
    const { result } = await mount()

    expect(result.current.violation).toBe(null)

    setFullscreenElement(null)
    fireFullscreenChange()
    // Nothing during the debounce — a transient state must not count.
    expect(result.current.violation).toBe(null)

    await vi.waitFor(() => expect(result.current.violation).toBe('exit'), {
      timeout: 1500,
    })
    expect(result.current.secondsLeft).toBe(FULLSCREEN_GRACE_SECONDS)
    expect(reportIntegrityEventMock).toHaveBeenCalledWith(
      'attempt-1',
      'fullscreen_exit',
      false,
    )
  })

  it('closes the attempt when the countdown runs out', async () => {
    const onTerminated = vi.fn()
    setFullscreenElement(document.documentElement)
    await mount({ onTerminated })

    setFullscreenElement(null)
    fireFullscreenChange()

    await vi.waitFor(
      () =>
        expect(reportIntegrityEventMock).toHaveBeenCalledWith(
          'attempt-1',
          'fullscreen_exit',
          true,
        ),
      { timeout: (FULLSCREEN_GRACE_SECONDS + 4) * 1000 },
    )
    await vi.waitFor(() => expect(onTerminated).toHaveBeenCalledTimes(1))
  })

  it('ignores a change that was flagged as intentional', async () => {
    setFullscreenElement(document.documentElement)
    const { result } = await mount()

    markIntentionalExamFullscreenExit()
    setFullscreenElement(null)
    fireFullscreenChange()

    await new Promise((r) => setTimeout(r, 800))

    expect(result.current.violation).toBe(null)
    expect(reportIntegrityEventMock).not.toHaveBeenCalled()
  })

  it('does not fire when the page still owns fullscreen on another element', async () => {
    setFullscreenElement(document.documentElement)
    const { result } = await mount()

    const video = document.createElement('video')
    setFullscreenElement(video)
    fireFullscreenChange()

    await new Promise((r) => setTimeout(r, 800))

    expect(result.current.violation).toBe(null)
    expect(reportIntegrityEventMock).not.toHaveBeenCalled()
  })

  it('clears the violation when fullscreen comes back in time', async () => {
    setFullscreenElement(document.documentElement)
    const { result } = await mount()

    setFullscreenElement(null)
    fireFullscreenChange()
    await vi.waitFor(() => expect(result.current.violation).toBe('exit'), {
      timeout: 1500,
    })

    setFullscreenElement(document.documentElement)
    fireFullscreenChange()
    await vi.waitFor(() => expect(result.current.violation).toBe(null), {
      timeout: 1500,
    })
    expect(result.current.secondsLeft).toBe(FULLSCREEN_GRACE_SECONDS)
  })
})

describe.skipIf(!EXAM_FULLSCREEN_ENFORCED)('useFullscreenGuard — page loaded outside fullscreen', () => {
  it('blocks and logs a reload, closing the F5 bypass', async () => {
    // A reload resumes the exam without any fullscreenchange to react to.
    setFullscreenElement(null)
    const { result } = await mount()

    await vi.waitFor(() => expect(result.current.violation).toBe('reload'), {
      timeout: 3000,
    })
    expect(reportIntegrityEventMock).toHaveBeenCalledWith(
      'attempt-1',
      'fullscreen_reload',
      false,
    )
  })

  it('never terminates the attempt, so a crashed machine costs nothing', async () => {
    const onTerminated = vi.fn()
    setFullscreenElement(null)
    const { result } = await mount({ onTerminated })

    await vi.waitFor(() => expect(result.current.violation).toBe('reload'), {
      timeout: 3000,
    })
    // Sit well past the grace window a deliberate exit would have.
    await new Promise((r) => setTimeout(r, (FULLSCREEN_GRACE_SECONDS + 2) * 1000))

    expect(result.current.violation).toBe('reload')
    expect(onTerminated).not.toHaveBeenCalled()
    expect(reportIntegrityEventMock).not.toHaveBeenCalledWith(
      'attempt-1',
      expect.anything(),
      true,
    )
  })

  it('is not upgraded to a terminating exit by a later event', async () => {
    const onTerminated = vi.fn()
    setFullscreenElement(null)
    const { result } = await mount({ onTerminated })

    await vi.waitFor(() => expect(result.current.violation).toBe('reload'), {
      timeout: 3000,
    })

    // Something fires a change while still outside fullscreen (a failed
    // request, say). The block must stay a block.
    fireFullscreenChange()
    await new Promise((r) => setTimeout(r, (FULLSCREEN_GRACE_SECONDS + 2) * 1000))

    expect(result.current.violation).toBe('reload')
    expect(onTerminated).not.toHaveBeenCalled()
  })

  it('clears once the student returns to fullscreen', async () => {
    setFullscreenElement(null)
    const { result } = await mount()

    await vi.waitFor(() => expect(result.current.violation).toBe('reload'), {
      timeout: 3000,
    })

    setFullscreenElement(document.documentElement)
    fireFullscreenChange()

    await vi.waitFor(() => expect(result.current.violation).toBe(null), {
      timeout: 1500,
    })
  })

  it('does not flag a legitimate start that reaches fullscreen', async () => {
    setFullscreenElement(document.documentElement)
    const { result } = await mount()

    // Sit through the initial check window with no events at all.
    await new Promise((r) => setTimeout(r, 2000))

    expect(result.current.violation).toBe(null)
    expect(reportIntegrityEventMock).not.toHaveBeenCalled()
  })

  it('stays out of the way where the page cannot go fullscreen (iOS Safari)', async () => {
    removeFullscreenSupport()
    setFullscreenElement(null)
    const { result } = await mount()

    await new Promise((r) => setTimeout(r, 2000))

    expect(result.current.violation).toBe(null)
    expect(reportIntegrityEventMock).not.toHaveBeenCalled()
  })

  it('is a no-op in preview mode', async () => {
    setFullscreenElement(null)
    const { result } = await mount({ isPreview: true })

    await new Promise((r) => setTimeout(r, 2000))

    expect(result.current.violation).toBe(null)
    expect(reportIntegrityEventMock).not.toHaveBeenCalled()
  })
})
