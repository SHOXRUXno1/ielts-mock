import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'
import {
  limitForTurn,
  VOICE_GATE,
  type RecordingLimit,
  type SpeakingTurnKind,
} from '../constants/recording-limits'
import { SPEAKING_AUDIO_CONSTRAINTS } from '../lib/mic-constraints'
import type { Phase } from '../types/phase'

/**
 * Summary of the microphone signal during the recording. `voiceDetected` is
 * the client-side "did we hear anything?" verdict — see VOICE_GATE.
 */
export type RecordingResult = {
  voiceDetected: boolean
  peakRms: number
  activeMs: number
  durationMs: number
}

type UseSpeakingRecorderOptions = {
  turnKind: SpeakingTurnKind
  onRecordingComplete: (
    blob: Blob,
    durationSeconds: number,
    result: RecordingResult,
  ) => void
  setPhase: (phase: Phase) => void
  onRecordStart?: () => void
  onRecordEnd?: () => void
}

const RMS_THRESHOLD = Math.pow(10, VOICE_GATE.RMS_THRESHOLD_DBFS / 20)

type VoiceGateState = {
  audioContext: AudioContext
  source: MediaStreamAudioSourceNode
  analyser: AnalyserNode
  buffer: Float32Array
  rafId: number | null
  lastSampleAt: number
  startedAt: number
  peakRms: number
  activeMs: number
}

export function useSpeakingRecorder({
  turnKind,
  onRecordingComplete,
  setPhase,
  onRecordStart,
  onRecordEnd,
}: UseSpeakingRecorderOptions) {
  const [recordingTime, setRecordingTime] = useState(0)
  const [recordingStream, setRecordingStream] = useState<MediaStream | null>(
    null,
  )

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const elapsedSecondsRef = useRef(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const pendingStreamRef = useRef<Promise<MediaStream> | null>(null)
  const turnKindRef = useRef(turnKind)
  const stopRecordingRef = useRef<() => void>(() => {})
  const onRecordEndRef = useRef(onRecordEnd)
  const startingRef = useRef(false)
  const voiceGateRef = useRef<VoiceGateState | null>(null)

  useEffect(() => {
    turnKindRef.current = turnKind
  }, [turnKind])

  useEffect(() => {
    onRecordEndRef.current = onRecordEnd
  }, [onRecordEnd])

  const recordingLimit: RecordingLimit = useMemo(
    () => limitForTurn(turnKind),
    [turnKind],
  )

  const recordingProgress = useMemo(
    () =>
      recordingLimit.hardSeconds > 0
        ? Math.min(100, (recordingTime / recordingLimit.hardSeconds) * 100)
        : 0,
    [recordingTime, recordingLimit.hardSeconds],
  )

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  /**
   * Sample RMS from the analyser at rAF rate and accumulate time above the
   * threshold. Runs while the recorder is running; stops itself once
   * `voiceGateRef.current` clears.
   */
  const tickVoiceGate = useCallback(() => {
    const gate = voiceGateRef.current
    if (!gate) return
    gate.analyser.getFloatTimeDomainData(gate.buffer)
    let sumSq = 0
    for (let i = 0; i < gate.buffer.length; i += 1) {
      const v = gate.buffer[i]
      sumSq += v * v
    }
    const rms = Math.sqrt(sumSq / gate.buffer.length)
    if (rms > gate.peakRms) gate.peakRms = rms
    const now = performance.now()
    const deltaMs = Math.min(64, now - gate.lastSampleAt)
    gate.lastSampleAt = now
    if (rms >= RMS_THRESHOLD) gate.activeMs += deltaMs
    gate.rafId = requestAnimationFrame(tickVoiceGate)
  }, [])

  const startVoiceGate = useCallback(
    (stream: MediaStream) => {
      if (voiceGateRef.current) return
      const AudioCtx =
        window.AudioContext ??
        (window as unknown as { webkitAudioContext?: typeof AudioContext })
          .webkitAudioContext
      if (!AudioCtx) return
      let ctx: AudioContext
      try {
        ctx = new AudioCtx()
      } catch {
        return
      }
      let source: MediaStreamAudioSourceNode
      try {
        source = ctx.createMediaStreamSource(stream)
      } catch {
        void ctx.close()
        return
      }
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 1024
      analyser.smoothingTimeConstant = 0
      source.connect(analyser)
      const now = performance.now()
      voiceGateRef.current = {
        audioContext: ctx,
        source,
        analyser,
        buffer: new Float32Array(analyser.fftSize),
        rafId: null,
        lastSampleAt: now,
        startedAt: now,
        peakRms: 0,
        activeMs: 0,
      }
      voiceGateRef.current.rafId = requestAnimationFrame(tickVoiceGate)
    },
    [tickVoiceGate],
  )

  const stopVoiceGate = useCallback((): RecordingResult => {
    const gate = voiceGateRef.current
    if (!gate) {
      // Analyser could not be created (unlikely — but we degrade to a
      // permissive verdict so recording still works).
      return { voiceDetected: true, peakRms: 0, activeMs: 0, durationMs: 0 }
    }
    if (gate.rafId !== null) cancelAnimationFrame(gate.rafId)
    const durationMs = performance.now() - gate.startedAt
    const { peakRms, activeMs } = gate
    try {
      gate.source.disconnect()
    } catch {
      // ignore
    }
    void gate.audioContext.close()
    voiceGateRef.current = null

    const voiceDetected =
      durationMs >= VOICE_GATE.MIN_DURATION_MS &&
      peakRms >= RMS_THRESHOLD &&
      activeMs >= VOICE_GATE.MIN_ACTIVE_MS

    return { voiceDetected, peakRms, activeMs, durationMs }
  }, [])

  /** Hand the microphone back to the browser. Only at the end of the session. */
  const releaseMic = useCallback(() => {
    clearTimer()
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    setRecordingStream(null)
  }, [clearTimer])

  useEffect(() => releaseMic, [releaseMic])

  /**
   * Open the microphone, or reuse the one already open.
   *
   * The device is deliberately held for the whole session. A freshly opened
   * capture device does not deliver usable audio immediately — echo
   * cancellation and automatic gain control need a moment to settle — so
   * reopening it per turn swallowed the first words of every answer. Short
   * replies suffered worst: candidates tapped, said their name, and Whisper,
   * handed near-silence, invented "Thank you." in its place.
   */
  const acquireStream = useCallback((): Promise<MediaStream> => {
    const open = streamRef.current
    if (open?.getAudioTracks().some((t) => t.readyState === 'live')) {
      return Promise.resolve(open)
    }
    // Callers overlap: the warm-up runs off a phase change while the candidate
    // may tap at any moment. Without sharing the request in flight each caller
    // sees no stream yet and opens the device again, orphaning handles that are
    // never released, and the microphone stops being grantable.
    const inFlight = pendingStreamRef.current
    if (inFlight) return inFlight

    // A stream whose tracks ended (device unplugged, OS took it away) is of no
    // use to MediaRecorder; drop it and ask for the device again.
    releaseMic()
    const request = navigator.mediaDevices
      .getUserMedia(SPEAKING_AUDIO_CONSTRAINTS)
      .then((stream) => {
        streamRef.current = stream
        setRecordingStream(stream)
        return stream
      })
      .finally(() => {
        pendingStreamRef.current = null
      })
    pendingStreamRef.current = request
    return request
  }, [releaseMic])

  /**
   * Start the device early, while the candidate is still reading or listening,
   * so it is settled by the time they speak. Failure is not reported: this is
   * speculative, and startRecording raises the real error if it matters.
   */
  const warmUpMic = useCallback(async () => {
    try {
      await acquireStream()
    } catch {
      // Left for startRecording to surface.
    }
  }, [acquireStream])

  const stopRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current
    if (!recorder || recorder.state !== 'recording') return

    clearTimer()

    onRecordEndRef.current?.()

    try {
      recorder.requestData()
    } catch {
      // ignore if unsupported
    }

    const voiceResult = stopVoiceGate()

    recorder.onstop = () => {
      const mimeType = recorder.mimeType || 'audio/webm'
      const blob = new Blob(chunksRef.current, { type: mimeType })
      const durationSeconds = elapsedSecondsRef.current
      // The microphone stays open for the next answer; see acquireStream.
      elapsedSecondsRef.current = 0
      setRecordingTime(0)
      onRecordingComplete(blob, durationSeconds, voiceResult)
    }
    recorder.stop()
  }, [clearTimer, onRecordingComplete, stopVoiceGate])

  useEffect(() => {
    stopRecordingRef.current = stopRecording
  }, [stopRecording])

  const startRecording = useCallback(async (): Promise<boolean> => {
    if (mediaRecorderRef.current?.state === 'recording') return false
    if (startingRef.current) return false

    startingRef.current = true
    try {
      const stream = await acquireStream()
      const recorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm',
      })
      chunksRef.current = []
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }
      recorder.start(100)
      mediaRecorderRef.current = recorder
      elapsedSecondsRef.current = 0
      setRecordingTime(0)
      startVoiceGate(stream)
      onRecordStart?.()

      // Read the limit once at start: the turn cannot change mid-recording,
      // and the interval closure must not capture a stale render's value.
      const { hardSeconds } = limitForTurn(turnKindRef.current)

      timerRef.current = setInterval(() => {
        setRecordingTime((t) => {
          const next = t + 1
          elapsedSecondsRef.current = next
          // The wrap-up cue has already been on screen for a while by now, so
          // the stop is expected — no toast on top of it.
          if (next >= hardSeconds) stopRecordingRef.current()
          return next
        })
      }, 1000)

      setPhase('recording')
      return true
    } catch {
      toast.error(
        'Microphone access denied — allow mic in browser settings, then tap to speak',
      )
      setPhase('ready')
      return false
    } finally {
      startingRef.current = false
    }
  }, [setPhase, onRecordStart, acquireStream, startVoiceGate])

  const abortRecording = useCallback(() => {
    clearTimer()
    stopVoiceGate()

    const recorder = mediaRecorderRef.current
    if (recorder) {
      if (recorder.state === 'recording') {
        recorder.onstop = null
        try {
          recorder.stop()
        } catch {
          // ignore if already stopped
        }
      }
      mediaRecorderRef.current = null
    }

    chunksRef.current = []
    releaseMic()
    setRecordingTime(0)
  }, [releaseMic, clearTimer, stopVoiceGate])

  return {
    recordingTime,
    recordingLimit,
    recordingProgress,
    recordingStream,
    startRecording,
    stopRecording,
    abortRecording,
    warmUpMic,
    releaseMic,
  }
}
