import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { renderHook } from 'vitest-browser-react'
import { getSimliToken } from '@/lib/api/speaking-examiner'
import type { Phase } from '../types/phase'
import {
  getSpeakingInitStateForTests,
  resetSpeakingInit,
  useSpeakingInit,
} from './use-speaking-init'

vi.mock('@/lib/api/speaking-examiner', () => ({
  getSimliToken: vi.fn(),
  formatSimliUnavailable: vi.fn(() => 'Simli unavailable'),
  getSimliFetchErrorMessage: vi.fn(() => 'Fetch error'),
}))

const mockToken = {
  enabled: true,
  session_token: 'session-token',
  face_id: 'face-id',
  ice_servers: null,
}

function createInitOptions(overrides: Partial<Parameters<typeof useSpeakingInit>[0]> = {}) {
  const beginLoading = vi.fn()
  const onSimliLoadingComplete = vi.fn()
  const handleSimliFallback = vi.fn()
  const phaseRef = { current: 'idle' as Phase }

  const options = {
    phase: 'idle' as Phase,
    phaseRef,
    simliEnabled: false,
    simliReady: false,
    simliFallback: false,
    beginLoading,
    onSimliLoadingComplete,
    handleSimliFallback,
    setSimliToken: vi.fn(),
    setSimliFaceId: vi.fn(),
    setSimliIceServers: vi.fn(),
    setSimliEnabled: vi.fn(),
    setPhase: vi.fn(),
    simliLoadTimeoutMs: 10_000,
    ...overrides,
  }

  return { options, beginLoading, onSimliLoadingComplete, handleSimliFallback, phaseRef }
}

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children)
  }

  return { queryClient, Wrapper }
}

describe('useSpeakingInit', () => {
  beforeEach(() => {
    resetSpeakingInit()
    vi.clearAllMocks()
    vi.mocked(getSimliToken).mockResolvedValue(mockToken)
  })

  it('fetches simli token once and calls beginLoading', async () => {
    const { options, beginLoading } = createInitOptions()
    const { Wrapper } = createWrapper()

    await renderHook(() => useSpeakingInit(options), { wrapper: Wrapper })

    await vi.waitFor(() => {
      expect(getSimliToken).toHaveBeenCalledOnce()
      expect(beginLoading).toHaveBeenCalledOnce()
    })
    expect(getSpeakingInitStateForTests().bootstrapped).toBe(true)
  })

  it('resetSpeakingInit clears module init flags', () => {
    resetSpeakingInit()
    const state = getSpeakingInitStateForTests()
    expect(state.bootstrapped).toBe(false)
    expect(state.loadingFinished).toBe(false)
  })

  it('restartInit resets flags and calls beginLoading again', async () => {
    const { options, beginLoading } = createInitOptions()
    const { Wrapper } = createWrapper()

    const { result, act } = await renderHook(() => useSpeakingInit(options), {
      wrapper: Wrapper,
    })

    await vi.waitFor(() => expect(beginLoading).toHaveBeenCalledOnce())

    resetSpeakingInit()

    await act(async () => {
      await result.current.restartInit()
    })

    expect(beginLoading).toHaveBeenCalledTimes(2)
  })

  it('completes loading after stable simliReady via double rAF', async () => {
    const rafCallbacks: FrameRequestCallback[] = []
    vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => {
      rafCallbacks.push(cb)
      return rafCallbacks.length
    })
    vi.stubGlobal('cancelAnimationFrame', vi.fn())

    const { options, onSimliLoadingComplete, phaseRef } = createInitOptions({
      phase: 'loading',
      simliEnabled: true,
      simliReady: true,
    })
    phaseRef.current = 'loading'
    const { Wrapper } = createWrapper()

    await renderHook(() => useSpeakingInit(options), { wrapper: Wrapper })

    expect(onSimliLoadingComplete).not.toHaveBeenCalled()

    rafCallbacks[0]?.(0)
    expect(onSimliLoadingComplete).not.toHaveBeenCalled()

    rafCallbacks[1]?.(0)
    expect(onSimliLoadingComplete).toHaveBeenCalledOnce()
    expect(getSpeakingInitStateForTests().loadingFinished).toBe(true)

    vi.unstubAllGlobals()
  })
})
