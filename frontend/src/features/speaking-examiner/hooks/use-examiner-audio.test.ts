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
    expect(result.current.simliFallback).toBe(true)
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

  describe('the caption waits for the voice', () => {
    it('stays quiet while the voice is still being synthesised', async () => {
      installSpeechSynthesisMock()
      let releaseSynthesis: (r: { audio_base64: string }) => void = () => {}
      vi.mocked(synthesizeExaminerTurn).mockReturnValue(
        new Promise((resolve) => {
          releaseSynthesis = resolve
        }),
      )

      const phaseRef = { current: 'thinking' as Phase }
      const onAudioStart = vi.fn()
      const { result, act } = await renderHook(() =>
        useExaminerAudio({ phaseRef, onAudioComplete: vi.fn(), onAudioStart }),
      )

      await act(() => {
        result.current.setSimliEnabled(true)
        result.current.handleSimliReady(true)
      })

      let played: Promise<void> | undefined
      await act(async () => {
        played = result.current.playExaminerAudio(
          'Where are you from?',
          '',
          undefined,
          { text: 'Where are you from?', part: 1 },
        )
        await Promise.resolve()
      })

      // A live turn arrives as text with no audio attached. This is the second
      // or so the candidate used to spend watching a still avatar under the
      // word "Speaking".
      expect(onAudioStart).not.toHaveBeenCalled()

      await act(async () => {
        releaseSynthesis({ audio_base64: 'AQID' })
        await played
      })

      expect(onAudioStart).toHaveBeenCalledOnce()
      expect(result.current.pendingAudioB64).toBe('AQID')
    })

    it('announces the start before the avatar is handed inline audio', async () => {
      installSpeechSynthesisMock()
      const order: string[] = []
      const phaseRef = { current: 'thinking' as Phase }
      const { result, act } = await renderHook(() =>
        useExaminerAudio({
          phaseRef,
          onAudioComplete: () => order.push('complete'),
          onAudioStart: () => order.push('start'),
        }),
      )

      await act(() => {
        result.current.setSimliEnabled(true)
        result.current.handleSimliReady(true)
      })

      await act(async () => {
        await result.current.playExaminerAudio('Good morning.', 'AQID')
      })

      expect(order).toEqual(['start'])
      expect(result.current.pendingAudioB64).toBe('AQID')
    })

    it('still announces the start on the browser-voice fallback', async () => {
      // Without this the turn strands: the completion is only honoured while
      // the phase says the examiner is speaking, and nothing else sets it.
      installSpeechSynthesisMock({ autoEnd: true })
      vi.mocked(synthesizeExaminerTurn).mockResolvedValue({ audio_base64: '' })

      const phaseRef = { current: 'thinking' as Phase }
      const onAudioComplete = vi.fn()
      const { result, act } = await renderHook(() =>
        useExaminerAudio({
          phaseRef,
          onAudioComplete,
          onAudioStart: () => {
            phaseRef.current = 'playing'
          },
        }),
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

      expect(onAudioComplete).toHaveBeenCalledOnce()
    })
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

  it('ignores onReady(false) during a live examiner turn', async () => {
    const phaseRef = { current: 'playing' as Phase }
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
})
