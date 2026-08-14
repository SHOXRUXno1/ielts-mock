import { memo, useCallback, useEffect, useRef, useState } from 'react'
import { SimliClient } from 'simli-client'
import { cn } from '@/lib/utils'
import {
  forEachPcmChunk,
  iceServersKey,
  mp3Base64ToPcm16,
  PCM_CHUNK_BYTES,
} from '../lib/simli-pcm'
import { LottieAvatar } from './lottie-avatar'

const CLOSE_COOLDOWN_MS = 2000
const MAX_CONNECT_ATTEMPTS = 2
const AUDIO_QUEUE_TIMEOUT_MS = 20_000

let sharedAudioContext: AudioContext | null = null
let lastSuccessfulCloseAt = 0

function getSharedAudioContext(): AudioContext {
  if (!sharedAudioContext || sharedAudioContext.state === 'closed') {
    sharedAudioContext = new AudioContext()
  }
  return sharedAudioContext
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

function SimliAvatarInner({
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
        const { pcm, duration } = await mp3Base64ToPcm16(
          b64,
          getSharedAudioContext(),
        )
        const numChunks = Math.ceil(pcm.length / PCM_CHUNK_BYTES)

        simliLog('[Simli] Audio duration:', duration, 'seconds')
        simliLog('[Simli] Sending audio data, chunks:', numChunks)

        client.ClearBuffer()
        if (audioRef.current) {
          audioRef.current.volume = 1
        }

        speakingDoneRef.current = false
        audioSentRef.current = true

        await forEachPcmChunk(pcm, PCM_CHUNK_BYTES, (chunk, index) => {
          if (simliRef.current !== client) return
          if (index === 0) {
            client.sendAudioDataImmediate(chunk)
          } else {
            client.sendAudioData(chunk)
          }
        })

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

  const flushQueuedAudioRef = useRef(flushQueuedAudio)
  const notifySpeakingDoneRef = useRef(notifySpeakingDone)
  const requestReconnectInternalRef = useRef(requestReconnect)

  useEffect(() => {
    flushQueuedAudioRef.current = flushQueuedAudio
  }, [flushQueuedAudio])

  useEffect(() => {
    notifySpeakingDoneRef.current = notifySpeakingDone
  }, [notifySpeakingDone])

  useEffect(() => {
    requestReconnectInternalRef.current = requestReconnect
  }, [requestReconnect])

  const iceKey = iceServersKey(iceServers)
  const iceServersRef = useRef(iceServers)

  useEffect(() => {
    iceServersRef.current = iceServers
  }, [iceServers])

  useEffect(() => {
    if (!sessionToken || !faceId) return

    let cancelled = false
    let client: SimliClient | null = null
    let startedSuccessfully = false

    const stopClient = (c: SimliClient) => {
      try {
        c.stop()
      } catch {
        /* ignore */
      }
    }

    const startSimli = async () => {
      const wait = lastSuccessfulCloseAt
        ? Math.max(0, CLOSE_COOLDOWN_MS - (Date.now() - lastSuccessfulCloseAt))
        : 0
      if (wait) {
        await new Promise((r) => setTimeout(r, wait))
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
            iceServersRef.current ?? null,
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
            notifySpeakingDoneRef.current()
          })

          client.on('error', (detail: string) => {
            simliError('[Simli] Error:', detail)
            if (readyRef.current) {
              requestReconnectInternalRef.current(
                queuedAudioRef.current ?? lastAudioRef.current,
              )
            }
          })

          client.on('startup_error', (message: string) => {
            simliError('[Simli] Startup error:', message)
            if (readyRef.current) {
              requestReconnectInternalRef.current(
                queuedAudioRef.current ?? lastAudioRef.current,
              )
            }
          })

          await client.start()
          if (cancelled) {
            stopClient(client)
            return
          }
          startedSuccessfully = true

          if (audioRef.current) {
            audioRef.current.volume = 0
          }

          simliLog('[Simli] Connected — video stream active')
          reconnectPendingRef.current = false
          setReady(true)
          onReadyRef.current?.(true)
          if (queuedAudioRef.current) {
            void flushQueuedAudioRef.current()
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
      if (startedSuccessfully) {
        lastSuccessfulCloseAt = Date.now()
      }
      simliRef.current = null
      setReady(false)
      onReadyRef.current?.(false)
    }
  }, [sessionToken, faceId, iceKey, clearEndTimer, activateLottieFallback])

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
        disablePictureInPicture
        disableRemotePlayback
        aria-label='Examiner video avatar'
        className={cn(
          'h-full w-full object-cover [transform:translateZ(0)] [backface-visibility:hidden] will-change-transform',
          ready ? 'opacity-100' : 'opacity-0',
        )}
      />
      <audio ref={audioRef} autoPlay playsInline />
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

function simliAvatarPropsEqual(
  prev: SimliAvatarProps,
  next: SimliAvatarProps,
): boolean {
  return (
    prev.sessionToken === next.sessionToken &&
    prev.faceId === next.faceId &&
    iceServersKey(prev.iceServers) === iceServersKey(next.iceServers) &&
    prev.audioBase64 === next.audioBase64 &&
    prev.isSpeaking === next.isSpeaking &&
    prev.isListening === next.isListening &&
    prev.suppressConnectingUI === next.suppressConnectingUI &&
    prev.className === next.className
  )
}

export const SimliAvatar = memo(SimliAvatarInner, simliAvatarPropsEqual)

SimliAvatar.displayName = 'SimliAvatar'
