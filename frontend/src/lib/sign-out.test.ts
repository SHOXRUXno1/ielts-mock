import { QueryClient } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuthStore } from '@/stores/auth-store'
import {
  clearLocalSession,
  handleUnauthorizedQueryError,
  hasAccessToken,
  loginSearchFromLocation,
} from './sign-out'

describe('sign-out helpers', () => {
  beforeEach(() => {
    useAuthStore.getState().auth.reset()
  })

  it('clearLocalSession resets auth and drops cached queries', async () => {
    const queryClient = new QueryClient()
    useAuthStore.getState().auth.setAccessToken('session')
    queryClient.setQueryData(['student-dashboard'], { tests_taken: 1 })

    clearLocalSession(queryClient)

    expect(useAuthStore.getState().auth.accessToken).toBe('')
    expect(queryClient.getQueryData(['student-dashboard'])).toBeUndefined()
  })

  it('treats a 401 after logout as noise', () => {
    const queryClient = new QueryClient()
    const navigate = vi.fn()

    expect(hasAccessToken()).toBe(false)
    expect(
      handleUnauthorizedQueryError(queryClient, '/student/profile', navigate),
    ).toBe(false)
    expect(navigate).not.toHaveBeenCalled()
  })

  it('clears the session and replaces to login when a live token gets 401', () => {
    const queryClient = new QueryClient()
    const navigate = vi.fn()
    useAuthStore.getState().auth.setAccessToken('session')
    queryClient.setQueryData(['student-dashboard'], { tests_taken: 1 })

    expect(
      handleUnauthorizedQueryError(
        queryClient,
        '/student/profile',
        navigate,
      ),
    ).toBe(true)

    expect(useAuthStore.getState().auth.accessToken).toBe('')
    expect(queryClient.getQueryData(['student-dashboard'])).toBeUndefined()
    expect(navigate).toHaveBeenCalledWith({
      to: '/login',
      replace: true,
      search: { redirect: '/student/profile' },
    })
  })

  it('omits an unsafe redirect from login search', () => {
    expect(loginSearchFromLocation('https://evil.example/phish')).toEqual({})
    expect(loginSearchFromLocation('/student/tests')).toEqual({
      redirect: '/student/tests',
    })
  })
})
