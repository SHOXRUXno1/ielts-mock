import { useCallback, useEffect, useRef, useState, type MutableRefObject } from 'react'
import { toast } from 'sonner'
import {
  synthesizeExaminerTurn,
  type SynthesizeTurnResponse,
} from '@/lib/api/speaking-examiner'
import { isLiveSpeakingPhase } from '../lib/is-live-phase'
import { iceServersKey } from '../lib/simli-pcm'
import type { Phase } from '../types/phase'

// Hard fallback ceiling if we can't decode the audio to measure its duration.
// The primary safety timer is duration-aware (see the effect below).
const PLAYING_SAFETY_TIMEOUT_MS = 45_000
// Extra time after the audio's natural end before we force phase off 'playing'.
// Covers Simli's own decode + WebRTC jitter + reasonable network wobble. Small
// enough that a stuck turn resolves in single-digit seconds, big enough to not
// cut off a normal end-of-turn Simli 'silent' event landing a beat late.
const DURATION_END_MARGIN_MS = 2500
// If the metadata probe fails to fire loadedmetadata quickly, fall back to the
// hard ceiling. The probe usually resolves in <200ms.
const METADATA_PROBE_TIMEOUT_MS = 3000
// The Livekit transport we use since PR #17 takes longer to bring up than
// the previous P2P path: WebSocket signal + LiveKit room join + WebRTC
// negotiation + first video frame typically land at 6-12s on this stack.
// The old 10s ceiling clipped that on any slower cold start, and our
// watchdog fell back to audio-only + remount the SimliClient, which then
// asked for a fresh /simli-token and started the whole cycle again — the
// three tokens-in-eight-seconds pattern from prod logs. 20 s gives an
// honest run a chance to finish while still bailing out when Simli is
// actually down.
const SIMLI_LOAD_TIMEOUT_MS = 20_000

type UseExaminerAudioOptions = {
  phaseRef: MutableRefObject<Phase>
  onAudioComplete: () => void
  /**
   * Called at the last moment before sound is produced, on every path.
   *
   * A live turn arrives as text with no audio attached; the voice takes a second
   * round trip to synthesise. The caption used to say the examiner was speaking
   * from the moment the text arrived, so the candidate watched a still avatar
   * under the word "Speaking" for a second or two of every question. Announcing
   * the start here instead ties the caption to the sound.
   */
  onAudioStart?: () => void
}

export function useExaminerAudio({
  phaseRef,
  onAudioComplete,
  onAudioStart,
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
  const onAudioStartRef = useRef(onAudioStart)

  useEffect(() => {
    onAudioCompleteRef.current = onAudioComplete
  }, [onAudioComplete])

  useEffect(() => {
    onAudioStartRef.current = onAudioStart
  }, [onAudioStart])

  const announceAudioStart = useCallback(() => {
    onAudioStartRef.current?.()
  }, [])

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
      if (
        !ready &&
        (phaseRef.current === 'loading' ||
          isLiveSpeakingPhase(phaseRef.current))
      ) {
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

  const setSimliIceServersStable = useCallback(
    (servers: RTCIceServer[] | null) => {
      setSimliIceServers((prev) =>
        iceServersKey(prev) === iceServersKey(servers) ? prev : servers,
      )
    },
    [],
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
        announceAudioStart()
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
    [announceAudioStart],
  )

  const speakWithWebSpeech = useCallback(
    (text: string): Promise<void> =>
      new Promise((resolve) => {
        // Announced before the capability check on purpose: a browser without
        // speech synthesis still has to move the turn along, and the caller
        // only completes a turn it was told had started.
        announceAudioStart()
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
    [cancelBrowserSpeech, announceAudioStart],
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

    // Deterministic phase-level end-of-turn signal, decoupled from Simli's
    // `silent` event. Every path into Simli goes through here, and Simli's
    // silent event has proved unreliable across turns (keepalive silent PCM
    // extends the buffer, WebRTC jitter, occasional missing 'silent' fires).
    // We probe the MP3's own duration off-DOM and fire handleSimliDone at
    // `duration + DURATION_END_MARGIN_MS`. Simli's silent event still gets
    // there first on the happy path; this is the always-armed backstop.
    let cancelled = false
    let mainTimer: number | null = null
    let fallbackTimer: number | null = null
    let objectUrl: string | null = null
    let probe: HTMLAudioElement | null = null

    const trigger = () => {
      if (phaseRef.current === 'playing') {
        handleSimliDone()
      }
    }

    const arm = (delayMs: number) => {
      if (cancelled || mainTimer !== null) return
      mainTimer = window.setTimeout(trigger, Math.max(0, delayMs))
    }

    try {
      const raw = atob(pendingAudioB64)
      const bytes = new Uint8Array(raw.length)
      for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i)
      const blob = new Blob([bytes], { type: 'audio/mpeg' })
      objectUrl = URL.createObjectURL(blob)

      probe = new Audio()
      probe.preload = 'metadata'
      probe.muted = true
      probe.src = objectUrl

      probe.onloadedmetadata = () => {
        if (cancelled) return
        const seconds = probe?.duration
        if (typeof seconds === 'number' && Number.isFinite(seconds) && seconds > 0) {
          arm(seconds * 1000 + DURATION_END_MARGIN_MS)
        } else {
          arm(PLAYING_SAFETY_TIMEOUT_MS)
        }
      }
      probe.onerror = () => {
        if (cancelled) return
        arm(PLAYING_SAFETY_TIMEOUT_MS)
      }

      // Belt-and-braces: if loadedmetadata never fires (browser quirk on some
      // MP3 payloads), don't leave the turn without a backstop.
      fallbackTimer = window.setTimeout(() => {
        if (cancelled || mainTimer !== null) return
        arm(PLAYING_SAFETY_TIMEOUT_MS)
      }, METADATA_PROBE_TIMEOUT_MS)
    } catch {
      arm(PLAYING_SAFETY_TIMEOUT_MS)
    }

    return () => {
      cancelled = true
      if (mainTimer !== null) window.clearTimeout(mainTimer)
      if (fallbackTimer !== null) window.clearTimeout(fallbackTimer)
      if (probe) {
        probe.onloadedmetadata = null
        probe.onerror = null
        probe.src = ''
      }
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
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
              announceAudioStart()
              setPendingAudioB64(synth.audio_base64)
              if (synth.tts_error) {
                toast.warning(`Examiner voice fallback — ${synth.tts_error}`)
              }
            } else {
              if (synth.tts_error) {
                toast.warning(`Examiner voice fallback — ${synth.tts_error}`)
              }
              // Browser TTS cannot move Simli's mouth — drop the still
              // video so the candidate is not watching a frozen face.
              handleSimliFallback()
              await speakWithWebSpeech(text)
              handleSimliDone()
            }
          } catch {
            handleSimliFallback()
            await speakWithWebSpeech(text)
            handleSimliDone()
          }
          return
        }

        if (hasAudio) {
          announceAudioStart()
          setPendingAudioB64(audioBase64)
        } else {
          const detail =
            ttsError ??
            (import.meta.env.DEV
              ? 'ElevenLabs returned no audio — check backend logs'
              : 'Voice service unavailable')
          toast.warning(`Examiner voice fallback — ${detail}`)
          handleSimliFallback()
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
      handleSimliFallback,
      announceAudioStart,
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

  /** Play a cached phrase through a plain <audio> element, bypassing Simli.
   *
   * After the Part 2 preparation timer runs, the Simli WebRTC session has
   * been idle for ~65 seconds and is often idle-closed by the network. Sending
   * "begin speaking" through Simli then triggers a reconnect mid-audio: the
   * old peer is torn down while the sound is queued, and the candidate hears
   * either a truncated cue or nothing at all. Playing this one short cached
   * MP3 directly reaches the ear on every attempt and leaves the Simli slot
   * to reconnect on its own beat for the next real examiner turn.
   */
  const playPhraseDirect = useCallback(
    async (audioBase64: string) => {
      cancelBrowserSpeech()
      setPendingAudioB64(null)
      await playBase64Audio(audioBase64)
      onAudioCompleteRef.current()
    },
    [cancelBrowserSpeech, playBase64Audio],
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
    setSimliIceServers: setSimliIceServersStable,
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
    playPhraseDirect,
    playSystemPhrase,
    resetAudioState,
    cancelBrowserSpeech,
    SIMLI_LOAD_TIMEOUT_MS,
  }
}
