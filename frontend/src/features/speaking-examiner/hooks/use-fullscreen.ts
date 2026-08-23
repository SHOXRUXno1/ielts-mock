import { useCallback, useEffect, useRef, useState } from 'react'
import { markIntentionalExamFullscreenExit } from '@/features/tests/take/exam-fullscreen'

type FullscreenElement = HTMLElement & {
  webkitRequestFullscreen?: () => Promise<void>
}

function getFullscreenElement(): Element | null {
  return (
    document.fullscreenElement ??
    (document as Document & { webkitFullscreenElement?: Element })
      .webkitFullscreenElement ??
    null
  )
}

async function requestFullscreen(el: FullscreenElement) {
  if (el.requestFullscreen) {
    await el.requestFullscreen()
    return
  }
  await el.webkitRequestFullscreen?.()
}

async function exitFullscreen() {
  if (document.exitFullscreen) {
    await document.exitFullscreen()
    return
  }
  await (
    document as Document & { webkitExitFullscreen?: () => Promise<void> }
  ).webkitExitFullscreen?.()
}

/**
 * Hook used by the examiner video for its own fullscreen toggle.
 *
 * The tricky part is that the exam page as a whole is already fullscreen
 * (documentElement). Naively calling exitFullscreen() to shrink the video
 * would leave the exam entirely, tripping the integrity guard and closing
 * the attempt. So the exit is treated as a *swap* back to documentElement,
 * and both legs of the swap are marked as intentional so the guard's
 * debounce window cannot catch the transient state.
 */
export function useFullscreen() {
  const ref = useRef<HTMLDivElement>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  // Remember whether the *page* was fullscreen before the video entered its
  // own. If it was, shrinking the video should give the page back.
  const restoreDocumentFullscreenRef = useRef(false)

  useEffect(() => {
    const sync = () => {
      setIsFullscreen(getFullscreenElement() === ref.current)
    }

    document.addEventListener('fullscreenchange', sync)
    document.addEventListener('webkitfullscreenchange', sync)
    return () => {
      document.removeEventListener('fullscreenchange', sync)
      document.removeEventListener('webkitfullscreenchange', sync)

      // Component unmounted with the video still fullscreen: give the page
      // back to whichever surface owned fullscreen before, so the exam does
      // not lose its own fullscreen just because the student moved off the
      // Speaking route.
      if (getFullscreenElement() === ref.current) {
        markIntentionalExamFullscreenExit()
        void exitFullscreen()
          .then(() => {
            if (restoreDocumentFullscreenRef.current) {
              markIntentionalExamFullscreenExit()
              return requestFullscreen(
                document.documentElement as FullscreenElement,
              )
            }
          })
          .catch(() => {})
      }
    }
  }, [])

  const toggle = useCallback(async () => {
    const el = ref.current as FullscreenElement | null
    if (!el) return

    try {
      if (getFullscreenElement() === el) {
        // Shrinking: hand fullscreen back to the exam page if it had it.
        markIntentionalExamFullscreenExit()
        await exitFullscreen()
        if (restoreDocumentFullscreenRef.current) {
          restoreDocumentFullscreenRef.current = false
          markIntentionalExamFullscreenExit()
          await requestFullscreen(
            document.documentElement as FullscreenElement,
          )
        }
      } else {
        // Enlarging: remember whether the page owns fullscreen so we can
        // hand it back on the next toggle.
        restoreDocumentFullscreenRef.current =
          getFullscreenElement() === document.documentElement
        markIntentionalExamFullscreenExit()
        await requestFullscreen(el)
      }
    } catch {
      // Fullscreen may be unavailable (e.g. iOS restrictions)
    }
  }, [])

  return { ref, isFullscreen, toggle }
}
