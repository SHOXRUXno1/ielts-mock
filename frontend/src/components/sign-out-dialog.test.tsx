import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { userEvent } from 'vitest/browser'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/auth-store'
import { SignOutDialog } from './sign-out-dialog'

const navigate = vi.fn()

vi.mock('@tanstack/react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-router')>()
  return {
    ...actual,
    useNavigate: () => navigate,
  }
})

vi.mock('@/lib/api/auth', () => ({
  logout: () => Promise.resolve(),
}))

function renderDialog() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <SignOutDialog open onOpenChange={vi.fn()} />
    </QueryClientProvider>,
  )
}

describe('SignOutDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useAuthStore.getState().auth.setAccessToken('session')
  })

  it('clears the session and replaces to login without a bounce-back redirect', async () => {
    const { getByRole } = await renderDialog()

    await userEvent.click(getByRole('button', { name: /^Sign out$/i }))

    await vi.waitFor(() => {
      expect(useAuthStore.getState().auth.accessToken).toBe('')
      expect(navigate).toHaveBeenCalledWith({
        to: '/login',
        replace: true,
      })
    })
  })

  it('does not call reset or navigate when Cancel is clicked', async () => {
    const { getByRole } = await renderDialog()

    await userEvent.click(getByRole('button', { name: /^Cancel$/i }))

    expect(useAuthStore.getState().auth.accessToken).toBe('session')
    expect(navigate).not.toHaveBeenCalled()
  })

  afterEach(() => {
    useAuthStore.getState().auth.reset()
  })
})
