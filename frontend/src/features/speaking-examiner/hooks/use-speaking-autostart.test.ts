import { beforeEach, describe, expect, it, vi } from 'vitest'
import { renderHook } from 'vitest-browser-react'
import type { Phase } from '../types/phase'
import {
  canAutostartSpeaking,
  markUserActivationForTests,
  resetUserActivationForTests,
} from '../lib/user-activation'
import { useSpeakingAutostart } from './use-speaking-autostart'

vi.mock('../lib/user-activation', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/user-activation')>()
  return {
    ...actual,
    canAutostartSpeaking: vi.fn(actual.canAutostartSpeaking),
  }
})

describe('useSpeakingAutostart', () => {
  beforeEach(() => {
    resetUserActivationForTests()
    markUserActivationForTests()
    vi.clearAllMocks()
    vi.mocked(canAutostartSpeaking).mockReturnValue(true)
  })

  it('starts once from idle when enabled', async () => {
    const handleStart = vi.fn().mockResolvedValue(true)
    const checkMicrophone = vi.fn().mockResolvedValue(true)

    const { result } = await renderHook(() =>
      useSpeakingAutostart({
        enabled: true,
        phase: 'idle',
        isTokenPending: false,
        score: null,
        checkMicrophone,
        handleStart,
      }),
    )

    await vi.waitFor(() => {
      expect(checkMicrophone).toHaveBeenCalledWith({ silent: true })
      expect(handleStart).toHaveBeenCalledOnce()
    })

    expect(result.current.blockedReason).toBeNull()
  })

  it('does not restart after the first attempt (End Test safe)', async () => {
    const handleStart = vi.fn().mockResolvedValue(true)
    const checkMicrophone = vi.fn().mockResolvedValue(true)

    type Props = { phase: Phase }
    const { rerender } = await renderHook(
      (props: Props = { phase: 'idle' }) =>
        useSpeakingAutostart({
          enabled: true,
          phase: props.phase,
          isTokenPending: false,
          score: null,
          checkMicrophone,
          handleStart,
        }),
      { initialProps: { phase: 'idle' as Phase } },
    )

    await vi.waitFor(() => {
      expect(handleStart).toHaveBeenCalledOnce()
    })

    await rerender({ phase: 'done' })
    await rerender({ phase: 'idle' })

    await vi.waitFor(() => {
      expect(handleStart).toHaveBeenCalledOnce()
    })
  })

  it('sets blockedReason to mic when microphone is denied', async () => {
    const handleStart = vi.fn().mockResolvedValue(true)
    const checkMicrophone = vi.fn().mockResolvedValue(false)

    const { result } = await renderHook(() =>
      useSpeakingAutostart({
        enabled: true,
        phase: 'idle',
        isTokenPending: false,
        score: null,
        checkMicrophone,
        handleStart,
      }),
    )

    await vi.waitFor(() => {
      expect(result.current.blockedReason).toBe('mic')
    })

    expect(handleStart).not.toHaveBeenCalled()
  })

  it('sets blockedReason to activation when there is no user gesture', async () => {
    vi.mocked(canAutostartSpeaking).mockReturnValue(false)
    const handleStart = vi.fn().mockResolvedValue(true)
    const checkMicrophone = vi.fn().mockResolvedValue(true)

    const { result } = await renderHook(() =>
      useSpeakingAutostart({
        enabled: true,
        phase: 'idle',
        isTokenPending: false,
        score: null,
        checkMicrophone,
        handleStart,
      }),
    )

    await vi.waitFor(() => {
      expect(result.current.blockedReason).toBe('activation')
    })

    expect(checkMicrophone).not.toHaveBeenCalled()
    expect(handleStart).not.toHaveBeenCalled()
  })

  it('sets blockedReason to failed when handleStart returns false', async () => {
    const handleStart = vi.fn().mockResolvedValue(false)
    const checkMicrophone = vi.fn().mockResolvedValue(true)

    const { result } = await renderHook(() =>
      useSpeakingAutostart({
        enabled: true,
        phase: 'idle',
        isTokenPending: false,
        score: null,
        checkMicrophone,
        handleStart,
      }),
    )

    await vi.waitFor(() => {
      expect(result.current.blockedReason).toBe('failed')
    })
  })

  it('retry() re-attempts after a blocked autostart', async () => {
    vi.mocked(canAutostartSpeaking).mockReturnValue(false)
    const handleStart = vi.fn().mockResolvedValue(true)
    const checkMicrophone = vi.fn().mockResolvedValue(true)

    const { result, act } = await renderHook(() =>
      useSpeakingAutostart({
        enabled: true,
        phase: 'idle',
        isTokenPending: false,
        score: null,
        checkMicrophone,
        handleStart,
      }),
    )

    await vi.waitFor(() => {
      expect(result.current.blockedReason).toBe('activation')
    })

    vi.mocked(canAutostartSpeaking).mockReturnValue(true)

    await act(async () => {
      result.current.retry()
    })

    await vi.waitFor(() => {
      expect(handleStart).toHaveBeenCalledOnce()
      expect(result.current.blockedReason).toBeNull()
    })
  })

  it('waits until token is ready before starting', async () => {
    const handleStart = vi.fn().mockResolvedValue(true)
    const checkMicrophone = vi.fn().mockResolvedValue(true)

    type Props = { isTokenPending: boolean }
    const { rerender } = await renderHook(
      (props: Props = { isTokenPending: true }) =>
        useSpeakingAutostart({
          enabled: true,
          phase: 'idle',
          isTokenPending: props.isTokenPending,
          score: null,
          checkMicrophone,
          handleStart,
        }),
      { initialProps: { isTokenPending: true } },
    )

    expect(handleStart).not.toHaveBeenCalled()

    await rerender({ isTokenPending: false })

    await vi.waitFor(() => {
      expect(handleStart).toHaveBeenCalledOnce()
    })
  })

  it('autostarts on a fresh mount after a previous instance unmounted', async () => {
    const handleStart = vi.fn().mockResolvedValue(true)
    const checkMicrophone = vi.fn().mockResolvedValue(true)

    const first = await renderHook(() =>
      useSpeakingAutostart({
        enabled: true,
        phase: 'idle',
        isTokenPending: false,
        score: null,
        checkMicrophone,
        handleStart,
      }),
    )

    await vi.waitFor(() => {
      expect(handleStart).toHaveBeenCalledOnce()
    })
    first.unmount()

    const handleStart2 = vi.fn().mockResolvedValue(true)
    const checkMicrophone2 = vi.fn().mockResolvedValue(true)

    await renderHook(() =>
      useSpeakingAutostart({
        enabled: true,
        phase: 'idle',
        isTokenPending: false,
        score: null,
        checkMicrophone: checkMicrophone2,
        handleStart: handleStart2,
      }),
    )

    await vi.waitFor(() => {
      expect(handleStart2).toHaveBeenCalledOnce()
    })
  })
})
