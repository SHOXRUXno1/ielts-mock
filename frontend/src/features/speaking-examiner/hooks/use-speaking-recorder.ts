import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'
import {
  limitForTurn,
  type RecordingLimit,
  type SpeakingTurnKind,
} from '../constants/recording-limits'
import type { Phase } from '../types/phase'

type UseSpeakingRecorderOptions = {
  turnKind: SpeakingTurnKind
  onRecordingComplete: (blob: Blob) => void
  setPhase: (phase: Phase) => void
  onRecordStart?: () => void
  onRecordEnd?: () => void
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
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const turnKindRef = useRef(turnKind)
  const stopRecordingRef = useRef<() => void>(() => {})
  const onRecordEndRef = useRef(onRecordEnd)
  const startingRef = useRef(false)

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
  const acquireStream = useCallback(async (): Promise<MediaStream> => {
    const open = streamRef.current
    if (open?.getAudioTracks().some((t) => t.readyState === 'live')) return open

    // A stream whose tracks ended (device unplugged, OS took it away) is of no
    // use to MediaRecorder; drop it and ask for the device again.
    releaseMic()
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true },
    })
    streamRef.current = stream
    setRecordingStream(stream)
    return stream
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

    recorder.onstop = () => {
      const mimeType = recorder.mimeType || 'audio/webm'
      const blob = new Blob(chunksRef.current, { type: mimeType })
      // The microphone stays open for the next answer; see acquireStream.
      setRecordingTime(0)
      onRecordingComplete(blob)
    }
    recorder.stop()
  }, [clearTimer, onRecordingComplete])

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
      setRecordingTime(0)
      onRecordStart?.()

      // Read the limit once at start: the turn cannot change mid-recording,
      // and the interval closure must not capture a stale render's value.
      const { hardSeconds } = limitForTurn(turnKindRef.current)

      timerRef.current = setInterval(() => {
        setRecordingTime((t) => {
          const next = t + 1
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
  }, [setPhase, onRecordStart, acquireStream])

  const abortRecording = useCallback(() => {
    clearTimer()

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
  }, [releaseMic, clearTimer])

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
