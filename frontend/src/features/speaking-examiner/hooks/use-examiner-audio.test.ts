import { beforeEach, describe, expect, it, vi } from 'vitest'
import { renderHook } from 'vitest-browser-react'
import { synthesizeExaminerTurn } from '@/lib/api/speaking-examiner'
import type { Phase } from '../types/phase'
import { useExaminerAudio } from './use-examiner-audio'

vi.mock('@/lib/api/speaking-examiner', () => ({
  synthesizeExaminerTurn: vi.fn(),
}))

vi.mock('sonner', () => ({
  toast: {
    warning: vi.fn(),
    error: vi.fn(),
  },
}))

function installSpeechSynthesisMock(options?: { autoEnd?: boolean }) {
  const speak = vi.fn((utterance: SpeechSynthesisUtterance) => {
    if (options?.autoEnd) {
      queueMicrotask(() => utterance.onend?.({} as SpeechSynthesisEvent))
    }
  })
  const cancel = vi.fn()
  Object.defineProperty(window, 'speechSynthesis', {
    configurable: true,
    writable: true,
    value: { speak, cancel, getVoices: () => [] },
  })
  return { speak, cancel }
}

describe('useExaminerAudio', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    installSpeechSynthesisMock()
  })

  it('does not start Web Speech preview while synthesizing for Simli', async () => {
    const { speak, cancel } = installSpeechSynthesisMock()
    vi.mocked(synthesizeExaminerTurn).mockResolvedValue({
      audio_base64: 'AQID',
    })

    const phaseRef = { current: 'playing' as Phase }
    const onAudioComplete = vi.fn()
    const { result, act } = await renderHook(() =>
      useExaminerAudio({ phaseRef, onAudioComplete }),
    )

    await act(() => {
      result.current.setSimliEnabled(true)
      result.current.handleSimliReady(true)
    })

    await act(async () => {
      await result.current.playExaminerAudio('', '', undefined, {
        text: 'Where are you from?',
        part: 1,
      })
    })

    expect(synthesizeExaminerTurn).toHaveBeenCalledOnce()
    expect(speak).not.toHaveBeenCalled()
    expect(cancel).toHaveBeenCalled()
    expect(result.current.pendingAudioB64).toBe('AQID')
  })

  it('falls back to Web Speech only when synthesize returns no audio', async () => {
    const { speak } = installSpeechSynthesisMock({ autoEnd: true })
    vi.mocked(synthesizeExaminerTurn).mockResolvedValue({
      audio_base64: '',
      tts_error: 'ElevenLabs unavailable',
    })

    const phaseRef = { current: 'playing' as Phase }
    const onAudioComplete = vi.fn()
    const { result, act } = await renderHook(() =>
      useExaminerAudio({ phaseRef, onAudioComplete }),
    )

    await act(() => {
      result.current.setSimliEnabled(true)
      result.current.handleSimliReady(true)
    })

    await act(async () => {
      await result.current.playExaminerAudio('', '', undefined, {
        text: 'Where are you from?',
        part: 1,
      })
    })

    expect(synthesizeExaminerTurn).toHaveBeenCalledOnce()
    expect(speak).toHaveBeenCalledOnce()
    expect(onAudioComplete).toHaveBeenCalledOnce()
    expect(result.current.pendingAudioB64).toBeNull()
  })

  it('cancelBrowserSpeech clears an active utterance', async () => {
    const { speak, cancel } = installSpeechSynthesisMock()
    let capturedUtterance: SpeechSynthesisUtterance | null = null
    speak.mockImplementation((utterance: SpeechSynthesisUtterance) => {
      capturedUtterance = utterance
    })

    const phaseRef = { current: 'ready' as Phase }
    const { result, act } = await renderHook(() =>
      useExaminerAudio({ phaseRef, onAudioComplete: vi.fn() }),
    )

    await act(async () => {
      void result.current.playSystemPhrase('Hello')
      await Promise.resolve()
      result.current.cancelBrowserSpeech()
      capturedUtterance?.onend?.({} as SpeechSynthesisEvent)
    })

    expect(cancel).toHaveBeenCalled()
    expect(speak).toHaveBeenCalledOnce()
  })

  it('handleSimliDone cancels browser speech before completing', async () => {
    const { cancel } = installSpeechSynthesisMock()
    const phaseRef = { current: 'playing' as Phase }
    const onAudioComplete = vi.fn()
    const { result, act } = await renderHook(() =>
      useExaminerAudio({ phaseRef, onAudioComplete }),
    )

    await act(() => {
      result.current.handleSimliDone()
    })

    expect(cancel).toHaveBeenCalled()
    expect(onAudioComplete).toHaveBeenCalledOnce()
  })

  it('ignores onReady(false) while phase is loading', async () => {
    const phaseRef = { current: 'loading' as Phase }
    const { result, act } = await renderHook(() =>
      useExaminerAudio({ phaseRef, onAudioComplete: vi.fn() }),
    )

    await act(() => {
      result.current.handleSimliReady(true)
    })
    expect(result.current.simliReady).toBe(true)

    await act(() => {
      result.current.handleSimliReady(false)
    })
    expect(result.current.simliReady).toBe(true)
  })

  it('applies onReady(false) after loading phase', async () => {
    const phaseRef = { current: 'idle' as Phase }
    const { result, act } = await renderHook(() =>
      useExaminerAudio({ phaseRef, onAudioComplete: vi.fn() }),
    )

    await act(() => {
      result.current.handleSimliReady(true)
      result.current.handleSimliReady(false)
    })

    expect(result.current.simliReady).toBe(false)
  })
})
