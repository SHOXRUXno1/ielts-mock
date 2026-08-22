import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { userEvent } from 'vitest/browser'
import { render } from 'vitest-browser-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { downloadResultPdf } from '@/lib/api/attempts'
import { AttemptRowActions } from './attempt-row-actions'

vi.mock('@/lib/api/attempts', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api/attempts')>(
    '@/lib/api/attempts',
  )
  return {
    ...actual,
    downloadResultPdf: vi.fn(),
    deleteAttempt: vi.fn(),
  }
})

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-router')>(
    '@tanstack/react-router',
  )
  return {
    ...actual,
    Link: ({ children }: { children: ReactNode }) => <a href='#'>{children}</a>,
  }
})

function renderActions(status?: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <AttemptRowActions attemptId='attempt-1' status={status} />
    </QueryClientProvider>,
  )
}

describe('AttemptRowActions', () => {
  beforeEach(() => {
    vi.mocked(downloadResultPdf).mockReset()
    vi.mocked(downloadResultPdf).mockResolvedValue(undefined)
  })

  it('downloads the PDF when Download PDF is selected', async () => {
    const screen = await renderActions('fully_scored')
    await userEvent.click(screen.getByRole('button', { name: 'Actions' }))
    const item = screen.getByRole('menuitem', { name: /Download PDF/i })
    await expect.element(item).toBeInTheDocument()
    await userEvent.click(item)
    expect(downloadResultPdf).toHaveBeenCalledWith('attempt-1')
  })

  it('disables the Download PDF item when the attempt is still in progress', async () => {
    const screen = await renderActions('in_progress')
    await userEvent.click(screen.getByRole('button', { name: 'Actions' }))
    const item = screen.getByRole('menuitem', { name: /Download PDF/i })
    await expect.element(item).toHaveAttribute('aria-disabled', 'true')
    expect(downloadResultPdf).not.toHaveBeenCalled()
  })

  it('keeps the Download PDF item disabled while the request is in flight', async () => {
    vi.mocked(downloadResultPdf).mockImplementation(() => new Promise(() => {}))
    const screen = await renderActions('fully_scored')
    await userEvent.click(screen.getByRole('button', { name: 'Actions' }))
    const item = screen.getByRole('menuitem', { name: /Download PDF/i })
    await userEvent.click(item)
    await expect.element(item).toHaveAttribute('aria-disabled', 'true')
    expect(downloadResultPdf).toHaveBeenCalledTimes(1)
  })
})
