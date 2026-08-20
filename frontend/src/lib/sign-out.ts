import type { QueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/auth-store'
import { parseSafeRedirect } from '@/lib/safe-redirect'

export const loginReplaceOptions = {
  to: '/login',
  replace: true,
} as const

export function clearLocalSession(queryClient: QueryClient): void {
  void queryClient.cancelQueries()
  useAuthStore.getState().auth.reset()
  queryClient.clear()
}

export function hasAccessToken(): boolean {
  return Boolean(useAuthStore.getState().auth.accessToken)
}

export function loginSearchFromLocation(href: string): { redirect?: string } {
  const redirect = parseSafeRedirect(href)
  return redirect ? { redirect } : {}
}

/**
 * Handle an unexpected 401 while a session still exists.
 * Returns false when the token is already gone (intentional logout).
 */
export function handleUnauthorizedQueryError(
  queryClient: QueryClient,
  currentHref: string,
  navigate: (opts: {
    to: '/login'
    replace: true
    search: { redirect?: string }
  }) => void,
): boolean {
  if (!hasAccessToken()) return false
  clearLocalSession(queryClient)
  navigate({
    ...loginReplaceOptions,
    search: loginSearchFromLocation(currentHref),
  })
  return true
}
