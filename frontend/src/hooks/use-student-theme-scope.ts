import { useLayoutEffect } from 'react'

/**
 * Marks student-only routes so their dark palette can stay independent from
 * the admin theme while still reaching document-level portals.
 */
export function useStudentThemeScope(active: boolean) {
  useLayoutEffect(() => {
    if (!active) return

    const root = document.documentElement
    root.dataset.studentTheme = 'active'

    return () => {
      delete root.dataset.studentTheme
    }
  }, [active])
}
