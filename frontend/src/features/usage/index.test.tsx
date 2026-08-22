import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fetchUsage, type UsageResponse } from '@/lib/api/usage'
import { Usage } from './index'

vi.mock('@/lib/api/usage', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api/usage')>(
    '@/lib/api/usage',
  )
  return { ...actual, fetchUsage: vi.fn() }
})

vi.mock('@/components/layout/header', () => ({
  Header: () => null,
}))
vi.mock('@/components/profile-dropdown', () => ({
  ProfileDropdown: () => null,
}))
vi.mock('@/components/config-drawer', () => ({
  ConfigDrawer: () => null,
}))
vi.mock('@/components/theme-switch', () => ({
  ThemeSwitch: () => null,
}))

const PAYLOAD: UsageResponse = {
  generated_at: '2026-08-23T00:00:00Z',
  providers: [
    {
      name: 'DigitalOcean',
      configured: true,
      status: 'warning',
      unit: 'USD',
      month_to_date_usage: '11.21',
      account_balance: '12.23',
      month_to_date_balance: '23.44',
      generated_at: '2026-08-23T00:00:00Z',
    },
    {
      name: 'ElevenLabs',
      configured: true,
      status: 'ok',
      unit: 'characters',
      tier: 'creator',
      used: 40_000,
      limit: 100_000,
      remaining: 60_000,
      percent_left: 60,
    },
    {
      name: 'Simli',
      configured: false,
      status: 'unknown',
      detail: 'No API key configured',
    },
  ],
}

/** A configured provider that cannot report numbers must explain itself. */
const NO_NUMBERS: UsageResponse = {
  generated_at: '2026-08-23T00:00:00Z',
  providers: [
    {
      name: 'ElevenLabs',
      configured: true,
      status: 'unknown',
      detail:
        "The API key cannot read the subscription (needs the 'user_read' permission). Speech synthesis is unaffected.",
    },
    {
      name: 'Gemini',
      configured: true,
      status: 'ok',
      model: 'gemini-3.1-flash-lite',
      key_count: 1,
      rpm_per_key: 300,
      used: 42,
      limit: null,
      remaining: null,
      percent_left: null,
      rate_limited_today: 0,
      estimated: true,
      detail:
        'Google publishes no quota endpoint. Set GEMINI_DAILY_QUOTA_PER_KEY to see a remaining figure; the free tier allows 1500/day per key.',
    },
  ],
}

async function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return await render(
    <QueryClientProvider client={qc}>
      <Usage />
    </QueryClientProvider>,
  )
}

describe('Usage page', () => {
  beforeEach(() => {
    vi.mocked(fetchUsage).mockReset()
  })

  it('shows the amount due and spend for DigitalOcean', async () => {
    vi.mocked(fetchUsage).mockResolvedValue(PAYLOAD)
    const screen = await renderPage()

    await expect.element(screen.getByText('DigitalOcean')).toBeInTheDocument()
    await expect.element(screen.getByText('$23.44')).toBeInTheDocument()
    await expect.element(screen.getByText('$11.21')).toBeInTheDocument()
  })

  it('shows remaining quota as a percentage for ElevenLabs', async () => {
    vi.mocked(fetchUsage).mockResolvedValue(PAYLOAD)
    const screen = await renderPage()

    await expect.element(screen.getByText('60%')).toBeInTheDocument()
    await expect
      .element(screen.getByText('60,000 characters left'))
      .toBeInTheDocument()
  })

  it('marks a provider without a key as not set up rather than empty', async () => {
    vi.mocked(fetchUsage).mockResolvedValue(PAYLOAD)
    const screen = await renderPage()

    await expect.element(screen.getByText('Simli')).toBeInTheDocument()
    await expect.element(screen.getByText('Not set up')).toBeInTheDocument()
    await expect
      .element(screen.getByText('No API key configured'))
      .toBeInTheDocument()
  })

  it('explains why ElevenLabs has no numbers instead of showing blank rows', async () => {
    vi.mocked(fetchUsage).mockResolvedValue(NO_NUMBERS)
    const screen = await renderPage()

    await expect
      .element(screen.getByText(/needs the 'user_read' permission/))
      .toBeInTheDocument()
    // The blank-row version of this card rendered these labels with dashes.
    expect(screen.getByText('Plan limit').elements().length).toBe(0)
  })

  it('shows calls made when Gemini has no stated daily quota', async () => {
    vi.mocked(fetchUsage).mockResolvedValue(NO_NUMBERS)
    const screen = await renderPage()

    await expect.element(screen.getByText('Calls today')).toBeInTheDocument()
    await expect.element(screen.getByText('42')).toBeInTheDocument()
    // No invented percentage, because no allowance was stated.
    expect(screen.getByText('100%').elements().length).toBe(0)
  })

  it('reports a failure instead of rendering empty cards', async () => {
    vi.mocked(fetchUsage).mockRejectedValue(new Error('403'))
    const screen = await renderPage()

    await expect
      .element(screen.getByText('Could not load usage data'))
      .toBeInTheDocument()
  })
})
