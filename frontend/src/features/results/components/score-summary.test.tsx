import { beforeEach, describe, expect, it, vi } from 'vitest'
import { userEvent } from 'vitest/browser'
import { render } from 'vitest-browser-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DirectionProvider } from '@/context/direction-provider'
import { downloadResultPdf, type AttemptDetailRead } from '@/lib/api/attempts'
import { ScoreSummary } from './score-summary'

vi.mock('@/lib/api/attempts', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api/attempts')>(
    '@/lib/api/attempts',
  )
  return {
    ...actual,
    downloadResultPdf: vi.fn(),
  }
})

const attempt: AttemptDetailRead = {
  id: 'attempt-1',
  test_id: 'test-1',
  status: 'fully_scored',
  mode: 'full_mock',
  practice_section_id: null,
  practice_part_number: null,
  practice_section_type: null,
  practice_correct: null,
  practice_total: null,
  started_at: '2026-08-19T07:00:00.000Z',
  finished_at: '2026-08-19T10:00:00.000Z',
  overall_band: 7,
  listening_band: 7.5,
  reading_band: 7,
  writing_band: 6.5,
  speaking_band: 6,
  listening_raw: 32,
  reading_raw: 30,
  flagged_overtime: false,
  created_at: '2026-08-19T07:00:00.000Z',
  updated_at: '2026-08-19T10:00:00.000Z',
  answers: [],
  evaluation_jobs: [],
  speaking_session: null,
  test_title: 'Cambridge IELTS 15 – Test 1',
}

function renderSummary() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <DirectionProvider>
      <QueryClientProvider client={qc}>
        <ScoreSummary attempt={attempt} scoringActive={false} />
      </QueryClientProvider>
    </DirectionProvider>,
  )
}

describe('ScoreSummary', () => {
  beforeEach(() => {
    vi.mocked(downloadResultPdf).mockReset()
    vi.mocked(downloadResultPdf).mockResolvedValue(undefined)
  })

  it('renders the download button and requests a PDF', async () => {
    const screen = await renderSummary()
    const button = screen.getByRole('button', { name: 'Download PDF' })
    await expect.element(button).toBeInTheDocument()
    await userEvent.click(button)
    expect(downloadResultPdf).toHaveBeenCalledWith('attempt-1')
  })

  it('disables the button while the PDF is generating', async () => {
    vi.mocked(downloadResultPdf).mockImplementation(() => new Promise(() => {}))
    const screen = await renderSummary()
    const button = screen.getByRole('button', { name: 'Download PDF' })
    await userEvent.click(button)
    await expect.element(button).toBeDisabled()
  })
})
