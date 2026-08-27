import { describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import {
  TakeTestTimerProvider,
  useTakeTestTimer,
} from './take-test-timer-context'

describe('exam timer isolation', () => {
  it('does not re-render a sibling when the countdown ticks', async () => {
    const tickRenders = { n: 0 }
    const bodyRenders = { n: 0 }
    const endsAt = new Date(Date.now() + 120_000).toISOString()

    function Ticker() {
      tickRenders.n += 1
      useTakeTestTimer()
      return <span>tick</span>
    }

    function Sibling() {
      bodyRenders.n += 1
      return <span>body</span>
    }

    const screen = await render(
      <TakeTestTimerProvider endsAt={endsAt} skewMs={0} enabled>
        <Ticker />
        <Sibling />
      </TakeTestTimerProvider>,
    )

    await expect.element(screen.getByText('body')).toBeVisible()

    const bodyAfterMount = bodyRenders.n
    const tickAfterMount = tickRenders.n
    expect(bodyAfterMount).toBeGreaterThan(0)
    expect(tickAfterMount).toBeGreaterThan(0)

    await vi.waitFor(() => {
      expect(tickRenders.n).toBeGreaterThan(tickAfterMount)
    })

    expect(bodyRenders.n).toBe(bodyAfterMount)
  })
})
