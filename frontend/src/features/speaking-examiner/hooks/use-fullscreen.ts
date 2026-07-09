import { useCallback, useEffect, useRef, useState } from 'react'

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

export function useFullscreen() {
  const ref = useRef<HTMLDivElement>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)

  useEffect(() => {
    const sync = () => {
      setIsFullscreen(getFullscreenElement() === ref.current)
    }

    document.addEventListener('fullscreenchange', sync)
    document.addEventListener('webkitfullscreenchange', sync)
    return () => {
      document.removeEventListener('fullscreenchange', sync)
      document.removeEventListener('webkitfullscreenchange', sync)

      if (getFullscreenElement() === ref.current) {
        void exitFullscreen().catch(() => {})
      }
    }
  }, [])

  const toggle = useCallback(async () => {
    const el = ref.current as FullscreenElement | null
    if (!el) return

    try {
      if (getFullscreenElement() === el) {
        await exitFullscreen()
      } else {
        await requestFullscreen(el)
      }
    } catch {
      // Fullscreen may be unavailable (e.g. iOS restrictions)
    }
  }, [])

  return { ref, isFullscreen, toggle }
}
