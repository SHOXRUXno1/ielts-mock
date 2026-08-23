import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  consumeIntentionalExit,
  enterExamFullscreen,
  exitExamFullscreen,
  isExamFullscreen,
  markIntentionalExamFullscreenExit,
} from './exam-fullscreen'

function stubFullscreen(opts: {
  element?: Element | null
  request?: () => Promise<void>
  exit?: () => Promise<void>
}) {
  const request = opts.request ?? vi.fn().mockResolvedValue(undefined)
  const exit = opts.exit ?? vi.fn().mockResolvedValue(undefined)

  Object.defineProperty(document.documentElement, 'requestFullscreen', {
    configurable: true,
    writable: true,
    value: request,
  })
  Object.defineProperty(document, 'exitFullscreen', {
    configurable: true,
    writable: true,
    value: exit,
  })
  Object.defineProperty(document, 'fullscreenElement', {
    configurable: true,
    get: () => opts.element ?? null,
  })

  return { request, exit }
}

afterEach(() => {
  const el = document.documentElement as unknown as Record<string, unknown>
  const doc = document as unknown as Record<string, unknown>
  delete el.requestFullscreen
  delete doc.exitFullscreen
  delete doc.fullscreenElement
  // Do not leak the intentional-exit flag between tests.
  consumeIntentionalExit()
  vi.restoreAllMocks()
})

describe('exam fullscreen', () => {
  it('isExamFullscreen is false when the Fullscreen API is idle', () => {
    stubFullscreen({ element: null })
    expect(isExamFullscreen()).toBe(false)
  })

  it('enter is a no-op when already fullscreen', () => {
    const { request } = stubFullscreen({
      element: document.documentElement,
    })
    enterExamFullscreen()
    expect(request).not.toHaveBeenCalled()
  })

  it('enter requests fullscreen on documentElement', () => {
    const { request } = stubFullscreen({ element: null })
    enterExamFullscreen()
    expect(request).toHaveBeenCalledTimes(1)
  })

  it('exit is a no-op when not fullscreen', () => {
    const { exit } = stubFullscreen({ element: null })
    exitExamFullscreen()
    expect(exit).not.toHaveBeenCalled()
  })

  it('exit leaves fullscreen when the exam is fullscreen', () => {
    const { exit } = stubFullscreen({
      element: document.documentElement,
    })
    exitExamFullscreen()
    expect(exit).toHaveBeenCalledTimes(1)
  })

  it('exit swallows a rejected Fullscreen API call', () => {
    stubFullscreen({
      element: document.documentElement,
      exit: vi.fn().mockRejectedValue(new Error('blocked')),
    })
    expect(() => exitExamFullscreen()).not.toThrow()
  })

  it('exit marks the fullscreen change as intentional', () => {
    stubFullscreen({ element: document.documentElement })
    exitExamFullscreen()
    expect(consumeIntentionalExit()).toBe(true)
    // The flag is consumed on first read so the next real violation is caught.
    expect(consumeIntentionalExit()).toBe(false)
  })

  it('markIntentionalExamFullscreenExit lets callers opt in without exiting', () => {
    markIntentionalExamFullscreenExit()
    expect(consumeIntentionalExit()).toBe(true)
  })
})
