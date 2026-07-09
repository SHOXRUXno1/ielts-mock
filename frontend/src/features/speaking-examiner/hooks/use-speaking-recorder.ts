import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'

export const MAX_RECORDING_SECONDS: Record<number, number> = {
  1: 30,
  2: 120,
  3: 45,
}

import type { Phase } from '../types/phase'

type UseSpeakingRecorderOptions = {
  currentPart: number
  onRecordingComplete: (blob: Blob) => void
  setPhase: (phase: Phase) => void
  onRecordStart?: () => void
  onRecordEnd?: () => void
}

export function useSpeakingRecorder({
  currentPart,
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
  const currentPartRef = useRef(currentPart)
  const stopRecordingRef = useRef<() => void>(() => {})
  const onRecordEndRef = useRef(onRecordEnd)
  const startingRef = useRef(false)

  useEffect(() => {
    currentPartRef.current = currentPart
  }, [currentPart])

  useEffect(() => {
    onRecordEndRef.current = onRecordEnd
  }, [onRecordEnd])

  const maxRecordingSeconds =
    MAX_RECORDING_SECONDS[currentPart] ?? MAX_RECORDING_SECONDS[1]

  const recordingProgress = useMemo(
    () =>
      maxRecordingSeconds > 0
        ? Math.min(100, (recordingTime / maxRecordingSeconds) * 100)
        : 0,
    [recordingTime, maxRecordingSeconds],
  )

  const cleanupStream = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    setRecordingStream(null)
  }, [])

  useEffect(() => cleanupStream, [cleanupStream])

  const stopRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current
    if (!recorder || recorder.state !== 'recording') return

    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }

    onRecordEndRef.current?.()

    try {
      recorder.requestData()
    } catch {
      // ignore if unsupported
    }

    recorder.onstop = () => {
      const mimeType = recorder.mimeType || 'audio/webm'
      const blob = new Blob(chunksRef.current, { type: mimeType })
      cleanupStream()
      onRecordingComplete(blob)
    }
    recorder.stop()
  }, [cleanupStream, onRecordingComplete])

  useEffect(() => {
    stopRecordingRef.current = stopRecording
  }, [stopRecording])

  const startRecording = useCallback(async (): Promise<boolean> => {
    if (mediaRecorderRef.current?.state === 'recording') return false
    if (startingRef.current) return false

    startingRef.current = true
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      })
      streamRef.current = stream
      setRecordingStream(stream)
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

      const maxSec =
        MAX_RECORDING_SECONDS[currentPartRef.current] ?? MAX_RECORDING_SECONDS[1]

      timerRef.current = setInterval(() => {
        setRecordingTime((t) => {
          const next = t + 1
          if (next >= maxSec) {
            toast.info(`Maximum recording time (${maxSec}s) reached`)
            stopRecordingRef.current()
          }
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
  }, [setPhase, onRecordStart])

  const abortRecording = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }

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
    cleanupStream()
    setRecordingTime(0)
  }, [cleanupStream])

  return {
    recordingTime,
    maxRecordingSeconds,
    recordingProgress,
    recordingStream,
    startRecording,
    stopRecording,
    abortRecording,
    cleanupStream,
  }
}
