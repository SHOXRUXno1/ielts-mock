type FullscreenElement = HTMLElement & {
  webkitRequestFullscreen?: () => Promise<void>
}

type FullscreenDocument = Document & {
  webkitFullscreenElement?: Element
  webkitExitFullscreen?: () => Promise<void>
}

function fullscreenElement(): Element | null {
  const doc = document as FullscreenDocument
  return document.fullscreenElement ?? doc.webkitFullscreenElement ?? null
}

function requestFn(el: FullscreenElement): (() => Promise<void>) | undefined {
  const req = el.requestFullscreen ?? el.webkitRequestFullscreen
  return req ? req.bind(el) : undefined
}

function exitFn(): (() => Promise<void>) | undefined {
  const doc = document as FullscreenDocument
  const exit = document.exitFullscreen ?? doc.webkitExitFullscreen
  return exit ? exit.bind(document) : undefined
}

export function isExamFullscreen(): boolean {
  return fullscreenElement() != null
}

/** Enter browser fullscreen (F11-like). Must run from a user click. */
export function enterExamFullscreen(): void {
  if (isExamFullscreen()) return

  const req = requestFn(document.documentElement as FullscreenElement)
  if (!req) return
  void Promise.resolve(req()).catch(() => {
    // Denied or unsupported (iOS, iframe, etc.) — exam still starts.
  })
}

/**
 * Leave exam fullscreen. No-op if the page is not in the Fullscreen API
 * (true F11 browser chrome cannot be closed from JS).
 */
export function exitExamFullscreen(): void {
  if (!isExamFullscreen()) return

  const exit = exitFn()
  if (!exit) return
  void Promise.resolve(exit()).catch(() => {
    // Already left, or the UA blocked the call.
  })
}
