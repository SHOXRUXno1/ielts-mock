import { beforeEach, describe, expect, it, vi } from 'vitest'
import { renderHook } from 'vitest-browser-react'
import { scoreExaminerWithRetry } from '@/lib/api/speaking-examiner'
import { useSpeakingFlow } from './use-speaking-flow'

vi.mock('@/lib/api/speaking-examiner', () => ({
  scoreExaminerWithRetry: vi.fn(),
  isSpeakingAbortError: vi.fn(() => false),
}))

vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
    warning: vi.fn(),
  },
}))

describe('useSpeakingFlow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('starts in idle phase', async () => {
    const { result } = await renderHook(() =>
      useSpeakingFlow({ liveSessionId: null }),
    )
    expect(result.current.phase).toBe('idle')
  })

  it('resetFlow returns to idle and clears score', async () => {
    const { result, act } = await renderHook(() =>
      useSpeakingFlow({ liveSessionId: null }),
    )

    await act(() => {
      result.current.setPhase('done')
      result.current.resetFlow()
    })

    expect(result.current.phase).toBe('idle')
    expect(result.current.score).toBeNull()
    expect(result.current.scoredHistory).toBeNull()
  })

  it('runScoring snapshots history into scoredHistory', async () => {
    const history = [
      { role: 'examiner' as const, text: 'Hello' },
      { role: 'candidate' as const, text: 'Hi there' },
    ]
    const mockScore = {
      fluency_coherence: { band: 6, feedback: 'ok' },
      lexical_resource: { band: 6, feedback: 'ok' },
      grammatical_range: { band: 6, feedback: 'ok' },
      pronunciation: { band: 6, feedback: 'ok' },
      overall_band: 6,
      strengths: [],
      improvements: [],
      transcript: 'Hi there',
      conversation_history: history,
    }

    vi.mocked(scoreExaminerWithRetry).mockResolvedValue(mockScore)

    const { result, act } = await renderHook(() =>
      useSpeakingFlow({ liveSessionId: null }),
    )

    await act(async () => {
      await result.current.runScoring(history)
    })

    expect(result.current.scoredHistory).toEqual(history)
    expect(result.current.score).toEqual(mockScore)
  })

  it('runScoring does not set score when phase is no longer scoring', async () => {
    const mockScore = {
      fluency_coherence: { band: 6, feedback: 'ok' },
      lexical_resource: { band: 6, feedback: 'ok' },
      grammatical_range: { band: 6, feedback: 'ok' },
      pronunciation: { band: 6, feedback: 'ok' },
      overall_band: 6,
      strengths: [],
      improvements: [],
      transcript: '',
    }

    vi.mocked(scoreExaminerWithRetry).mockImplementation(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10))
      return mockScore
    })

    const { result, act } = await renderHook(() =>
      useSpeakingFlow({ liveSessionId: null }),
    )

    await act(async () => {
      const scoringPromise = result.current.runScoring([
        { role: 'examiner', text: 'Hello' },
      ])
      result.current.resetFlow()
      await scoringPromise
    })

    expect(result.current.phase).toBe('idle')
    expect(result.current.score).toBeNull()
  })
})
