import { useCallback, useEffect, useRef, useState } from 'react'
import { SimliClient } from 'simli-client'
import { cn } from '@/lib/utils'
import { LottieAvatar } from './lottie-avatar'

const TARGET_SAMPLE_RATE = 16000
const PCM_CHUNK_BYTES = 6000
const CLOSE_COOLDOWN_MS = 2000
const MAX_CONNECT_ATTEMPTS = 2
const AUDIO_QUEUE_TIMEOUT_MS = 20_000

let sharedAudioContext: AudioContext | null = null
let simliSessionFirstConnect = true

function getSharedAudioContext(): AudioContext {
  if (!sharedAudioContext || sharedAudioContext.state === 'closed') {
    sharedAudioContext = new AudioContext()
  }
  return sharedAudioContext
}

async function base64ToPcm16(
  base64: string
): Promise<{ pcm: Uint8Array; duration: number }> {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)

  const ctx = getSharedAudioContext()
  if (ctx.state === 'suspended') {
    await ctx.resume()
  }

  const audioBuffer = await ctx.decodeAudioData(bytes.buffer.slice(0))
  const duration = audioBuffer.duration

  const channelData = audioBuffer.getChannelData(0)
  let samples: Float32Array

  if (audioBuffer.sampleRate !== TARGET_SAMPLE_RATE) {
    const ratio = audioBuffer.sampleRate / TARGET_SAMPLE_RATE
    const newLength = Math.round(channelData.length / ratio)
    samples = new Float32Array(newLength)
    for (let i = 0; i < newLength; i++) {
      samples[i] = channelData[Math.min(Math.floor(i * ratio), channelData.length - 1)]
    }
  } else {
    samples = channelData
  }

  const pcm = new Uint8Array(samples.length * 2)
  const view = new DataView(pcm.buffer)
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]))
    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true)
  }

  return { pcm, duration }
}

function simliLog(...args: unknown[]) {
  if (!import.meta.env.DEV) return
  // eslint-disable-next-line no-console -- dev-only Simli diagnostics
  console.log(...args)
}

function simliError(...args: unknown[]) {
  if (!import.meta.env.DEV) return
  // eslint-disable-next-line no-console -- dev-only Simli diagnostics
  console.error(...args)
}

type SimliAvatarProps = {
  sessionToken: string
  faceId: string
  iceServers?: RTCIceServer[] | null
  audioBase64: string | null
  isSpeaking: boolean
  isListening?: boolean
  onSpeakingDone: () => void
  onReady?: (ready: boolean) => void
  onFallback?: () => void
  onConnectionLost?: () => void
  suppressConnectingUI?: boolean
  className?: string
}

export function SimliAvatar({
  sessionToken,
  faceId,
  iceServers,
  audioBase64,
  isSpeaking,
  isListening = false,
  onSpeakingDone,
  onReady,
  onFallback,
  onConnectionLost,
  suppressConnectingUI = false,
  className,
}: SimliAvatarProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const audioRef = useRef<HTMLAudioElement>(null)
  const simliRef = useRef<SimliClient | null>(null)
  const onSpeakingDoneRef = useRef(onSpeakingDone)
  const onReadyRef = useRef(onReady)
  const onFallbackRef = useRef(onFallback)
  const onConnectionLostRef = useRef(onConnectionLost)
  const lastAudioRef = useRef<string | null>(null)
  const queuedAudioRef = useRef<string | null>(null)
  const audioSentRef = useRef(false)
  const speakingDoneRef = useRef(false)
  const reconnectPendingRef = useRef(false)
  const endTimerRef = useRef<number | null>(null)
  const [ready, setReady] = useState(false)
  const [useLottieFallback, setUseLottieFallback] = useState(false)
  const [lottieSpeaking, setLottieSpeaking] = useState(false)

  useEffect(() => {
    onSpeakingDoneRef.current = onSpeakingDone
  }, [onSpeakingDone])

  useEffect(() => {
    onReadyRef.current = onReady
  }, [onReady])

  useEffect(() => {
    onFallbackRef.current = onFallback
  }, [onFallback])

  useEffect(() => {
    onConnectionLostRef.current = onConnectionLost
  }, [onConnectionLost])

  const clearEndTimer = useCallback(() => {
    if (endTimerRef.current !== null) {
      window.clearTimeout(endTimerRef.current)
      endTimerRef.current = null
    }
  }, [])

  const readyRef = useRef(false)

  useEffect(() => {
    readyRef.current = ready
  }, [ready])

  const requestReconnect = useCallback(
    (failedAudio?: string | null) => {
      if (reconnectPendingRef.current) return
      reconnectPendingRef.current = true
      if (failedAudio) {
        queuedAudioRef.current = failedAudio
        lastAudioRef.current = null
      }
      audioSentRef.current = false
      clearEndTimer()
      onConnectionLostRef.current?.()
    },
    [clearEndTimer],
  )

  const notifySpeakingDone = useCallback(() => {
    if (speakingDoneRef.current) return
    speakingDoneRef.current = true
    clearEndTimer()
    audioSentRef.current = false
    onSpeakingDoneRef.current()
  }, [clearEndTimer])

  const activateLottieFallback = useCallback(() => {
    setUseLottieFallback(true)
    onReadyRef.current?.(false)
    onFallbackRef.current?.()
  }, [])

  const playFallbackAudio = useCallback(
    async (b64: string) => {
      const binary = atob(b64)
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
      const blob = new Blob([bytes], { type: 'audio/mpeg' })
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      setLottieSpeaking(true)
      audio.onended = () => {
        URL.revokeObjectURL(url)
        setLottieSpeaking(false)
        onSpeakingDoneRef.current()
      }
      audio.onerror = () => {
        URL.revokeObjectURL(url)
        setLottieSpeaking(false)
        onSpeakingDoneRef.current()
      }
      await audio.play()
    },
    []
  )

  const sendAudioToSimli = useCallback(
    async (client: SimliClient, b64: string) => {
      try {
        const { pcm, duration } = await base64ToPcm16(b64)
        const numChunks = Math.ceil(pcm.length / PCM_CHUNK_BYTES)

        simliLog('[Simli] Audio duration:', duration, 'seconds')
        simliLog('[Simli] Sending audio data, chunks:', numChunks)

        client.ClearBuffer()
        if (audioRef.current) {
          audioRef.current.volume = 1
        }

        speakingDoneRef.current = false
        audioSentRef.current = true

        for (let i = 0; i < pcm.length; i += PCM_CHUNK_BYTES) {
          const chunk = pcm.slice(i, i + PCM_CHUNK_BYTES)
          if (i === 0) {
            client.sendAudioDataImmediate(chunk)
          } else {
            client.sendAudioData(chunk)
          }
        }

        clearEndTimer()
        endTimerRef.current = window.setTimeout(() => {
          if (audioSentRef.current) {
            simliLog('[Simli] Speaking end (duration timeout)')
            notifySpeakingDone()
          }
        }, (duration + 0.5) * 1000)
      } catch (err) {
        simliError('[Simli] Failed to send audio:', err)
        requestReconnect(b64)
      }
    },
    [clearEndTimer, notifySpeakingDone, requestReconnect]
  )

  const flushQueuedAudio = useCallback(async () => {
    const client = simliRef.current
    const b64 = queuedAudioRef.current
    if (!client || !b64 || b64 === lastAudioRef.current) return

    lastAudioRef.current = b64
    queuedAudioRef.current = null
    await sendAudioToSimli(client, b64)
  }, [sendAudioToSimli])

  useEffect(() => {
    if (!sessionToken || !faceId) return

    let cancelled = false
    let client: SimliClient | null = null

    const stopClient = (c: SimliClient) => {
      try {
        c.stop()
      } catch {
        /* ignore */
      }
    }

    const startSimli = async () => {
      const skipCooldown = simliSessionFirstConnect
      simliSessionFirstConnect = false
      if (!skipCooldown) {
        await new Promise((r) => setTimeout(r, CLOSE_COOLDOWN_MS))
      }
      if (cancelled) return

      const video = videoRef.current
      const audio = audioRef.current
      if (!video || !audio) return

      audio.volume = 0

      for (let attempt = 1; attempt <= MAX_CONNECT_ATTEMPTS; attempt++) {
        if (cancelled) return

        simliLog(`[Simli] Connecting (attempt ${attempt}/${MAX_CONNECT_ATTEMPTS})…`)

        try {
          client = new SimliClient(
            sessionToken,
            video,
            audio,
            iceServers ?? null,
            undefined,
            'p2p'
          )
          simliRef.current = client

          client.on('speaking', () => {
            simliLog('[Simli] Avatar speaking')
          })

          client.on('silent', () => {
            if (!audioSentRef.current) return
            simliLog('[Simli] Speaking end (silent event)')
            notifySpeakingDone()
          })

          client.on('error', (detail: string) => {
            simliError('[Simli] Error:', detail)
            if (readyRef.current) {
              requestReconnect(queuedAudioRef.current ?? lastAudioRef.current)
            }
          })

          client.on('startup_error', (message: string) => {
            simliError('[Simli] Startup error:', message)
            if (readyRef.current) {
              requestReconnect(queuedAudioRef.current ?? lastAudioRef.current)
            }
          })

          await client.start()
          if (cancelled) {
            stopClient(client)
            return
          }

          if (audioRef.current) {
            audioRef.current.volume = 0
          }

          simliLog('[Simli] Connected — video stream active')
          reconnectPendingRef.current = false
          setReady(true)
          onReadyRef.current?.(true)
          if (queuedAudioRef.current) {
            void flushQueuedAudio()
          }
          return
        } catch (err) {
          simliError(`[Simli] Attempt ${attempt} failed:`, err)
          if (client) {
            stopClient(client)
            client = null
            simliRef.current = null
          }
          if (attempt < MAX_CONNECT_ATTEMPTS) {
            await new Promise((r) => setTimeout(r, 1500))
          }
        }
      }

      if (!cancelled) {
        simliError('[Simli] All connection attempts failed — Lottie fallback')
        activateLottieFallback()
      }
    }

    void startSimli()

    const handleUnload = () => {
      if (client) stopClient(client)
    }
    window.addEventListener('beforeunload', handleUnload)
    window.addEventListener('pagehide', handleUnload)

    return () => {
      cancelled = true
      window.removeEventListener('beforeunload', handleUnload)
      window.removeEventListener('pagehide', handleUnload)
      clearEndTimer()
      if (client) stopClient(client)
      simliRef.current = null
      setReady(false)
      onReadyRef.current?.(false)
    }
  }, [
    sessionToken,
    faceId,
    iceServers,
    clearEndTimer,
    flushQueuedAudio,
    notifySpeakingDone,
    activateLottieFallback,
    requestReconnect,
  ])

  useEffect(() => {
    if (!audioBase64 || audioBase64 === lastAudioRef.current) return

    if (useLottieFallback) {
      lastAudioRef.current = audioBase64
      const timer = window.setTimeout(() => {
        void playFallbackAudio(audioBase64)
      }, 0)
      return () => window.clearTimeout(timer)
    }

    if (!ready || !simliRef.current) {
      simliLog('[Simli] Audio queued — waiting for connection')
      queuedAudioRef.current = audioBase64
      return
    }

    lastAudioRef.current = audioBase64
    void sendAudioToSimli(simliRef.current, audioBase64)
  }, [audioBase64, ready, useLottieFallback, playFallbackAudio, sendAudioToSimli])

  useEffect(() => {
    if (ready && queuedAudioRef.current && simliRef.current) {
      void flushQueuedAudio()
    }
  }, [ready, flushQueuedAudio])

  useEffect(() => {
    if (!audioBase64 || ready || useLottieFallback) return

    const timer = window.setTimeout(() => {
      const queued = queuedAudioRef.current
      if (!queued || ready) return
      simliError('[Simli] Audio queue timeout — falling back to local playback')
      activateLottieFallback()
      void playFallbackAudio(queued)
    }, AUDIO_QUEUE_TIMEOUT_MS)

    return () => window.clearTimeout(timer)
  }, [
    audioBase64,
    ready,
    useLottieFallback,
    activateLottieFallback,
    playFallbackAudio,
  ])

  if (useLottieFallback) {
    return (
      <LottieAvatar
        isSpeaking={isSpeaking || lottieSpeaking}
        isListening={isListening}
        className={className}
      />
    )
  }

  return (
    <div
      className={cn(
        'relative flex items-center justify-center overflow-hidden rounded-xl bg-muted',
        className
      )}
    >
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        aria-label='Examiner video avatar'
        className={cn(
          'h-full w-full object-cover transition-opacity duration-500',
          ready ? 'opacity-100' : 'opacity-0',
        )}
      />
      <audio ref={audioRef} autoPlay />
      {!ready && !suppressConnectingUI && (
        <div className='absolute inset-0 flex items-center justify-center'>
          <div className='flex flex-col items-center gap-2'>
            <div className='h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent' />
            <span className='text-xs text-muted-foreground'>
              Connecting avatar…
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
