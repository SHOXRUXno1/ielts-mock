import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { userEvent } from 'vitest/browser'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SectionDurationField } from './section-duration-field'
import type {
  DurationMode,
  SectionSettings,
  SectionType,
} from '../data/schema'

const updateSectionDuration = vi.fn()
const toastWarning = vi.fn()
const toastSuccess = vi.fn()

vi.mock('@/lib/api/section-settings', () => ({
  updateSectionDuration: (...args: unknown[]) => updateSectionDuration(...args),
}))

vi.mock('sonner', () => ({
  toast: {
    warning: (...args: unknown[]) => toastWarning(...args),
    success: (...args: unknown[]) => toastSuccess(...args),
    error: vi.fn(),
  },
}))

function settings(
  type: SectionType,
  minutes: number | null,
  mode: DurationMode = 'standard',
): SectionSettings[] {
  return [
    {
      id: `s-${type}`,
      test_id: 't1',
      section_type: type,
      duration_minutes: minutes,
      duration_mode: mode,
    },
  ]
}

async function renderField(
  type: SectionType,
  minutes: number | null,
  mode: DurationMode = 'standard',
) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const screen = await render(
    <QueryClientProvider client={qc}>
      <SectionDurationField
        testId='t1'
        sectionType={type}
        settings={settings(type, minutes, mode)}
      />
    </QueryClientProvider>,
  )
  return screen
}

function durationInput(screen: Awaited<ReturnType<typeof renderField>>) {
  return screen.container.querySelector(
    'input[type="number"]',
  ) as HTMLInputElement | null
}

describe('SectionDurationField', () => {
  beforeEach(() => {
    updateSectionDuration.mockReset()
    toastWarning.mockReset()
    toastSuccess.mockReset()
  })

  it('shows the saved duration for listening', async () => {
    const screen = await renderField('listening', 30)
    expect(durationInput(screen)?.value).toBe('30')
    await expect
      .element(screen.getByText(/Standard is recommended/))
      .toBeInTheDocument()
  })

  it('disables duration input in standard mode', async () => {
    const screen = await renderField('listening', 30, 'standard')
    expect(durationInput(screen)?.disabled).toBe(true)
  })

  it('enables duration input in custom mode and saves with mode', async () => {
    updateSectionDuration.mockResolvedValue({
      settings: settings('listening', 40, 'custom')[0],
      warning: 'Computer-delivered IELTS uses 30 min.',
    })
    const screen = await renderField('listening', 30, 'standard')

    await screen.getByLabelText('Custom').click()
    expect(durationInput(screen)?.disabled).toBe(false)

    await userEvent.fill(durationInput(screen)!, '40')
    await screen.getByRole('button', { name: 'Save section settings' }).click()

    await vi.waitFor(() => {
      expect(updateSectionDuration).toHaveBeenCalledWith('t1', 'listening', {
        duration_mode: 'custom',
        duration_minutes: 40,
      })
      expect(toastWarning).toHaveBeenCalled()
    })
  })

  it('blocks saving an out-of-range custom value', async () => {
    const screen = await renderField('listening', 30, 'custom')
    const input = durationInput(screen)
    expect(input).not.toBeNull()

    await userEvent.fill(input!, '10')

    await expect
      .element(screen.getByText(/Listening duration must be 20-45 min/))
      .toBeInTheDocument()
    const save = screen.getByRole('button', { name: 'Save section settings' })
    await expect.element(save).toBeDisabled()
    expect(updateSectionDuration).not.toHaveBeenCalled()
  })

  it('does not show Match audio length option', async () => {
    const screen = await renderField('listening', 30)
    expect(
      screen.container.textContent?.includes('Match audio length'),
    ).toBe(false)
  })

  it('shows AI-paced (untimed) for speaking without a hard cap', async () => {
    const screen = await renderField('speaking', null)

    await expect
      .element(screen.getByText('AI-paced (untimed)'))
      .toBeInTheDocument()
    expect(durationInput(screen)).toBeNull()

    await screen.getByRole('switch').click()
    expect(durationInput(screen)).not.toBeNull()
    expect(durationInput(screen)?.value).toBe('20')
  })
})
