/**
 * Only keep in-app paths. Full URLs are accepted when they match the
 * current origin (TanStack `history.location.href` is often absolute).
 */
export function parseSafeRedirect(raw: unknown): string | undefined {
  if (typeof raw !== 'string') return undefined
  const value = raw.trim()
  if (!value) return undefined

  if (isInternalPath(value)) return sanitizePath(value)

  try {
    const url = new URL(value, fallbackOrigin())
    if (url.origin !== fallbackOrigin()) return undefined
    const path = `${url.pathname}${url.search}${url.hash}`
    return isInternalPath(path) ? sanitizePath(path) : undefined
  } catch {
    return undefined
  }
}

function isInternalPath(value: string): boolean {
  return value.startsWith('/') && !value.startsWith('//')
}

function sanitizePath(path: string): string | undefined {
  if (path === '/login' || path.startsWith('/login?') || path.startsWith('/login#')) {
    return undefined
  }
  return path
}

function fallbackOrigin(): string {
  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin
  }
  return 'http://localhost'
}
