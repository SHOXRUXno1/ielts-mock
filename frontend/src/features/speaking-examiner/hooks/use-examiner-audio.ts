import { useCallback, useEffect, useRef, useState, type MutableRefObject } from 'react'
import { toast } from 'sonner'
import {
  synthesizeExaminerTurn,
  type SynthesizeTurnResponse,
} from '@/lib/api/speaking-examiner'
import type { Phase } from '../types/phase'

const PLAYING_SAFETY_TIMEOUT_MS = 120_000
const SIMLI_LOAD_TIMEOUT_MS = 10_000

type UseExaminerAudioOptions = {
  phaseRef: MutableRefObject<Phase>
  onAudioComplete: () => void
}

export function useExaminerAudio({
  phaseRef,
  onAudioComplete,
}: UseExaminerAudioOptions) {
  const [simliToken, setSimliToken] = useState<string | null>(null)
  const [simliFaceId, setSimliFaceId] = useState<string | null>(null)
  const [simliIceServers, setSimliIceServers] = useState<
    RTCIceServer[] | null
  >(null)
  const [simliEnabled, setSimliEnabled] = useState(false)
  const [simliReady, setSimliReady] = useState(false)
  const [simliFallback, setSimliFallback] = useState(false)
  const [pendingAudioB64, setPendingAudioB64] = useState<string | null>(null)

  const audioElRef = useRef<HTMLAudioElement | null>(null)
  const activeUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null)
  const simliEnabledRef = useRef(false)
  const simliReadyRef = useRef(false)
  const simliFallbackRef = useRef(false)
  const simliReadyWaitersRef = useRef<Array<(ok: boolean) => void>>([])
  const onAudioCompleteRef = useRef(onAudioComplete)

  useEffect(() => {
    onAudioCompleteRef.current = onAudioComplete
  }, [onAudioComplete])

  useEffect(() => {
    simliEnabledRef.current = simliEnabled
  }, [simliEnabled])

  useEffect(() => {
    simliReadyRef.current = simliReady
  }, [simliReady])

  useEffect(() => {
    simliFallbackRef.current = simliFallback
  }, [simliFallback])

  const cancelBrowserSpeech = useCallback(() => {
    const active = activeUtteranceRef.current
    if (active) {
      active.onend = null
      active.onerror = null
      activeUtteranceRef.current = null
    }
    window.speechSynthesis?.cancel()
    const el = audioElRef.current
    if (el) {
      el.pause()
      el.src = ''
      audioElRef.current = null
    }
  }, [])

  const handleSimliReady = useCallback(
    (ready: boolean) => {
      if (!ready && phaseRef.current === 'loading') {
        return
      }
      simliReadyRef.current = ready
      setSimliReady(ready)
      if (ready) {
        const waiters = simliReadyWaitersRef.current
        simliReadyWaitersRef.current = []
        waiters.forEach((fn) => fn(true))
      }
    },
    [phaseRef],
  )

  const handleSimliFallback = useCallback(() => {
    simliFallbackRef.current = true
    setSimliFallback(true)
    simliReadyRef.current = false
    setSimliReady(false)
    const waiters = simliReadyWaitersRef.current
    simliReadyWaitersRef.current = []
    waiters.forEach((fn) => fn(true))
  }, [])

  const waitForSimliReady = useCallback(
    (timeoutMs = SIMLI_LOAD_TIMEOUT_MS): Promise<boolean> => {
      if (!simliEnabledRef.current || simliFallbackRef.current) {
        return Promise.resolve(true)
      }
      if (simliReadyRef.current) return Promise.resolve(true)

      return new Promise((resolve) => {
        let settled = false
        const finish = (ok: boolean) => {
          if (settled) return
          settled = true
          window.clearTimeout(timer)
          simliReadyWaitersRef.current = simliReadyWaitersRef.current.filter(
            (w) => w !== finish,
          )
          resolve(ok)
        }
        const timer = window.setTimeout(() => finish(false), timeoutMs)
        simliReadyWaitersRef.current.push(finish)
      })
    },
    [],
  )

  const usesSimliPlayback = useCallback(
    () => simliEnabledRef.current && !simliFallbackRef.current,
    [],
  )

  const playBase64Audio = useCallback(
    (base64: string): Promise<void> =>
      new Promise((resolve) => {
        try {
          const raw = atob(base64)
          const bytes = new Uint8Array(raw.length)
          for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i)
          const blob = new Blob([bytes], { type: 'audio/mpeg' })
          const url = URL.createObjectURL(blob)
          const audio = new Audio(url)
          audioElRef.current = audio
          audio.onended = () => {
            URL.revokeObjectURL(url)
            audioElRef.current = null
            resolve()
          }
          audio.onerror = () => {
            URL.revokeObjectURL(url)
            audioElRef.current = null
            resolve()
          }
          audio.play().catch(() => {
            audioElRef.current = null
            resolve()
          })
        } catch {
          resolve()
        }
      }),
    [],
  )

  const speakWithWebSpeech = useCallback(
    (text: string): Promise<void> =>
      new Promise((resolve) => {
        if (!window.speechSynthesis) {
          resolve()
          return
        }
        cancelBrowserSpeech()
        const utterance = new SpeechSynthesisUtterance(text)
        utterance.lang = 'en-GB'
        utterance.rate = 0.9
        utterance.onend = () => {
          if (activeUtteranceRef.current === utterance) {
            activeUtteranceRef.current = null
          }
          resolve()
        }
        utterance.onerror = () => {
          if (activeUtteranceRef.current === utterance) {
            activeUtteranceRef.current = null
          }
          resolve()
        }
        activeUtteranceRef.current = utterance
        window.speechSynthesis.speak(utterance)
      }),
    [cancelBrowserSpeech],
  )

  const handleSimliDone = useCallback(() => {
    cancelBrowserSpeech()
    setPendingAudioB64(null)
    if (phaseRef.current === 'playing') {
      onAudioCompleteRef.current()
    }
  }, [phaseRef, cancelBrowserSpeech])

  useEffect(() => {
    if (!pendingAudioB64) return

    const timer = window.setTimeout(() => {
      if (
        phaseRef.current === 'playing' &&
        simliEnabledRef.current &&
        !simliFallbackRef.current
      ) {
        handleSimliDone()
      }
    }, PLAYING_SAFETY_TIMEOUT_MS)

    return () => window.clearTimeout(timer)
  }, [pendingAudioB64, phaseRef, handleSimliDone])

  const playExaminerAudio = useCallback(
    async (
      text: string,
      audioBase64: string,
      ttsError?: string | null,
      synthesize?: {
        text: string
        part: number
        cue_card?: string | null
        signal?: AbortSignal
      },
    ) => {
      const hasAudio = Boolean(audioBase64?.trim())

      if (usesSimliPlayback()) {
        cancelBrowserSpeech()
        const simliOk = await waitForSimliReady()
        if (!simliOk && import.meta.env.DEV) {
          // eslint-disable-next-line no-console -- dev-only Simli diagnostics
          console.warn('[Examiner] Simli not ready — audio may queue')
        }

        if (!hasAudio && synthesize) {
          try {
            const synth: SynthesizeTurnResponse = await synthesizeExaminerTurn(
              {
                text: synthesize.text,
                part: synthesize.part,
                cue_card: synthesize.cue_card,
              },
              synthesize.signal,
            )
            if (synth.audio_base64?.trim()) {
              setPendingAudioB64(synth.audio_base64)
              if (synth.tts_error) {
                toast.warning(`Examiner voice fallback — ${synth.tts_error}`)
              }
            } else {
              if (synth.tts_error) {
                toast.warning(`Examiner voice fallback — ${synth.tts_error}`)
              }
              await speakWithWebSpeech(text)
              handleSimliDone()
            }
          } catch {
            await speakWithWebSpeech(text)
            handleSimliDone()
          }
          return
        }

        if (hasAudio) {
          setPendingAudioB64(audioBase64)
        } else {
          const detail =
            ttsError ??
            (import.meta.env.DEV
              ? 'ElevenLabs returned no audio — check backend logs'
              : 'Voice service unavailable')
          toast.warning(`Examiner voice fallback — ${detail}`)
          await speakWithWebSpeech(text)
          handleSimliDone()
        }
        return
      }

      if (hasAudio) {
        await playBase64Audio(audioBase64)
      } else if (synthesize) {
        try {
          const synth = await synthesizeExaminerTurn(
            {
              text: synthesize.text,
              part: synthesize.part,
              cue_card: synthesize.cue_card,
            },
            synthesize.signal,
          )
          if (synth.audio_base64?.trim()) {
            await playBase64Audio(synth.audio_base64)
          } else {
            if (synth.tts_error) {
              toast.warning(`Examiner voice fallback — ${synth.tts_error}`)
            }
            await speakWithWebSpeech(text)
          }
        } catch {
          await speakWithWebSpeech(text)
        }
      } else {
        if (ttsError) {
          toast.warning(`Examiner voice fallback — ${ttsError}`)
        }
        await speakWithWebSpeech(text)
      }
      onAudioCompleteRef.current()
    },
    [
      usesSimliPlayback,
      waitForSimliReady,
      cancelBrowserSpeech,
      playBase64Audio,
      speakWithWebSpeech,
      handleSimliDone,
    ],
  )

  const playExaminerPhrase = useCallback(
    async (
      text: string,
      audioBase64: string,
      ttsError?: string | null,
    ) => {
      await playExaminerAudio(text, audioBase64, ttsError)
    },
    [playExaminerAudio],
  )

  const playSystemPhrase = useCallback(
    async (text: string) => {
      cancelBrowserSpeech()
      setPendingAudioB64(null)
      await speakWithWebSpeech(text)
      onAudioCompleteRef.current()
    },
    [cancelBrowserSpeech, speakWithWebSpeech],
  )

  const resetAudioState = useCallback(() => {
    cancelBrowserSpeech()
    setPendingAudioB64(null)
    simliReadyWaitersRef.current = []
    simliFallbackRef.current = false
    setSimliFallback(false)
    setSimliReady(false)
    simliReadyRef.current = false
  }, [cancelBrowserSpeech])

  return {
    simliToken,
    setSimliToken,
    simliFaceId,
    setSimliFaceId,
    simliIceServers,
    setSimliIceServers,
    simliEnabled,
    setSimliEnabled,
    simliReady,
    simliFallback,
    pendingAudioB64,
    handleSimliReady,
    handleSimliFallback,
    waitForSimliReady,
    usesSimliPlayback,
    handleSimliDone,
    playExaminerAudio,
    playExaminerPhrase,
    playSystemPhrase,
    resetAudioState,
    cancelBrowserSpeech,
    SIMLI_LOAD_TIMEOUT_MS,
  }
}
