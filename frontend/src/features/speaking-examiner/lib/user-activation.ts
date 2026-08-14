/**
 * Detect whether the document has sticky user activation (needed for
 * autoplay of Audio / getUserMedia in some browsers).
 *
 * Prefer the User Activation API; also track pointer/key gestures and an
 * explicit mark from Finish-section / section-switch clicks so Writing →
 * Speaking autostart works even when hasBeenActive is unreliable.
 */

const SPEAKING_GESTURE_KEY = 'speaking-autostart-gesture'

let fallbackActive = false
let listenersAttached = false

function markFallbackActive() {
  fallbackActive = true
}

function teardownFallbackListeners() {
  if (!listenersAttached || typeof document === 'undefined') return
  document.removeEventListener('pointerdown', markFallbackActive, true)
  document.removeEventListener('keydown', markFallbackActive, true)
  listenersAttached = false
}

function ensureFallbackListeners() {
  if (listenersAttached || typeof document === 'undefined') return
  document.addEventListener('pointerdown', markFallbackActive, true)
  document.addEventListener('keydown', markFallbackActive, true)
  listenersAttached = true
}

ensureFallbackListeners()

export function hasUserActivation(): boolean {
  if (typeof navigator !== 'undefined' && 'userActivation' in navigator) {
    const activation = (
      navigator as Navigator & {
        userActivation?: { hasBeenActive?: boolean }
      }
    ).userActivation
    if (activation?.hasBeenActive === true) return true
  }
  ensureFallbackListeners()
  return fallbackActive
}

/** Call from Finish section / confirm-switch click handlers before navigating to Speaking. */
export function markSpeakingAutostartGesture() {
  fallbackActive = true
  try {
    sessionStorage.setItem(SPEAKING_GESTURE_KEY, '1')
  } catch {
    /* private mode / disabled storage */
  }
}

/** True when autoplay is likely allowed for Speaking autostart. */
export function canAutostartSpeaking(): boolean {
  if (hasUserActivation()) return true
  try {
    return sessionStorage.getItem(SPEAKING_GESTURE_KEY) === '1'
  } catch {
    return fallbackActive
  }
}

/** @internal test helper */
export function resetUserActivationForTests() {
  fallbackActive = false
  teardownFallbackListeners()
  try {
    sessionStorage.removeItem(SPEAKING_GESTURE_KEY)
  } catch {
    /* ignore */
  }
  ensureFallbackListeners()
}

/** @internal test helper */
export function markUserActivationForTests() {
  fallbackActive = true
  try {
    sessionStorage.setItem(SPEAKING_GESTURE_KEY, '1')
  } catch {
    /* ignore */
  }
}
