import * as React from 'react'

const MOBILE_BREAKPOINT = 768
const MOBILE_QUERY = `(max-width: ${MOBILE_BREAKPOINT - 1}px)`

/** Matches Tailwind `lg` breakpoint (1024px). */
const DESKTOP_QUERY = '(min-width: 1024px)'

function useMediaQuery(query: string, serverSnapshot = false) {
  return React.useSyncExternalStore(
    (callback) => {
      const mql = window.matchMedia(query)
      mql.addEventListener('change', callback)
      return () => mql.removeEventListener('change', callback)
    },
    () => window.matchMedia(query).matches,
    () => serverSnapshot,
  )
}

export function useIsMobile() {
  return useMediaQuery(MOBILE_QUERY)
}

/** True at Tailwind `lg` and above — used for desktop split panes. */
export function useIsDesktop() {
  return useMediaQuery(DESKTOP_QUERY)
}
