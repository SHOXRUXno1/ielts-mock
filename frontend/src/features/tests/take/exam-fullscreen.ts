type FullscreenElement = HTMLElement & {
  webkitRequestFullscreen?: () => Promise<void>
}

type FullscreenDocument = Document & {
  webkitFullscreenElement?: Element
  webkitExitFullscreen?: () => Promise<void>
}

type KeyboardApi = {
  lock?: (keyCodes?: string[]) => Promise<void>
  unlock?: () => void
}

type NavigatorWithKeyboard = Navigator & { keyboard?: KeyboardApi }

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

function getKeyboardApi(): KeyboardApi | undefined {
  const nav = navigator as NavigatorWithKeyboard
  return nav.keyboard
}

/**
 * Set true whenever exam code itself triggers a fullscreen exit (test
 * finished, guard timed out, admin preview). The guard hook consults this to
 * tell an intentional exit from a rule violation, then resets it.
 *
 * A module-level flag beats a React ref: exits happen deep in submit handlers,
 * and threading a ref through every path is more error-prone than one gate.
 */
let intentionalExit = false

/** Called by exam code right before it initiates its own exit. */
export function markIntentionalExamFullscreenExit(): void {
  intentionalExit = true
}

/**
 * Read (and clear) the intentional-exit flag. The guard calls this each time
 * a fullscreenchange fires so a stale flag cannot silence a later violation.
 */
export function consumeIntentionalExit(): boolean {
  const v = intentionalExit
  intentionalExit = false
  return v
}

export function isExamFullscreen(): boolean {
  return fullscreenElement() != null
}

/**
 * Best-effort keyboard lock, hidden behind a helper so callers do not have to
 * feature-detect. Silently no-ops in Firefox and Safari (no support), on
 * insecure origins, and inside iframes.
 *
 * Locks Escape only: a full lock would also swallow Alt-Tab, which is far too
 * heavy-handed for a browser-based exam.
 */
async function tryLockEscape(): Promise<void> {
  const kb = getKeyboardApi()
  if (!kb?.lock) return
  try {
    await kb.lock(['Escape'])
  } catch {
    // Denied (not fullscreen yet, not focused, unsupported).
  }
}

function tryUnlock(): void {
  const kb = getKeyboardApi()
  if (!kb?.unlock) return
  try {
    kb.unlock()
  } catch {
    // Already unlocked, or the API is not really present.
  }
}

/** Enter browser fullscreen (F11-like). Must run from a user click. */
export function enterExamFullscreen(): void {
  if (isExamFullscreen()) {
    // Already in — still worth attempting the lock in case we re-entered.
    void tryLockEscape()
    return
  }

  const req = requestFn(document.documentElement as FullscreenElement)
  if (!req) return
  void Promise.resolve(req())
    .then(() => tryLockEscape())
    .catch(() => {
      // Denied or unsupported (iOS, iframe, etc.) — exam still starts.
    })
}

/**
 * Leave exam fullscreen. No-op if the page is not in the Fullscreen API
 * (true F11 browser chrome cannot be closed from JS).
 *
 * Marks the exit as intentional so the guard does not treat it as a
 * violation. Every exam code-path that leaves fullscreen (finish, submit,
 * timeout-forced termination) must go through this helper.
 */
export function exitExamFullscreen(): void {
  tryUnlock()
  if (!isExamFullscreen()) return

  markIntentionalExamFullscreenExit()
  const exit = exitFn()
  if (!exit) return
  void Promise.resolve(exit()).catch(() => {
    // Already left, or the UA blocked the call.
  })
}
