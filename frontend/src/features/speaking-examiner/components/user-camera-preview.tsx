import { useEffect, useRef } from 'react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

type UserCameraPreviewProps = {
  enabled: boolean
  isRecording?: boolean
  variant?: 'pip' | 'standalone'
  className?: string
}

const PREVIEW_CONSTRAINTS: MediaStreamConstraints = {
  video: {
    facingMode: 'user',
    width: { ideal: 320 },
    height: { ideal: 240 },
    frameRate: { ideal: 15 },
  },
  audio: false,
}

let sharedPreviewStream: MediaStream | null = null
let previewInFlight: Promise<MediaStream> | null = null
let previewRefCount = 0
let previewReleaseTimer: number | null = null

function clearPreviewReleaseTimer() {
  if (previewReleaseTimer !== null) {
    window.clearTimeout(previewReleaseTimer)
    previewReleaseTimer = null
  }
}

function stopSharedPreviewStream() {
  sharedPreviewStream?.getTracks().forEach((t) => t.stop())
  sharedPreviewStream = null
}

async function acquireSharedPreviewStream(): Promise<MediaStream> {
  if (sharedPreviewStream?.active) {
    return sharedPreviewStream
  }

  if (previewInFlight) {
    return previewInFlight
  }

  previewInFlight = navigator.mediaDevices
    .getUserMedia(PREVIEW_CONSTRAINTS)
    .then((stream) => {
      sharedPreviewStream = stream
      previewInFlight = null
      return stream
    })
    .catch((err) => {
      previewInFlight = null
      throw err
    })

  return previewInFlight
}

function releaseSharedPreviewStream() {
  previewRefCount = Math.max(0, previewRefCount - 1)
  if (previewRefCount > 0) return

  clearPreviewReleaseTimer()
  previewReleaseTimer = window.setTimeout(() => {
    if (previewRefCount <= 0) {
      stopSharedPreviewStream()
    }
    previewReleaseTimer = null
  }, 150)
}

/** @internal test helper */
export function resetSharedPreviewStreamForTests() {
  clearPreviewReleaseTimer()
  previewRefCount = 0
  previewInFlight = null
  stopSharedPreviewStream()
}

/** @internal test helper */
export function __testAcquireSharedPreviewStream() {
  return acquireSharedPreviewStream()
}

export function UserCameraPreview({
  enabled,
  isRecording = false,
  variant = 'pip',
  className,
}: UserCameraPreviewProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  useEffect(() => {
    if (!enabled) {
      streamRef.current = null
      if (videoRef.current) {
        videoRef.current.srcObject = null
      }
      return
    }

    let cancelled = false
    clearPreviewReleaseTimer()
    previewRefCount += 1
    const videoEl = videoRef.current

    void acquireSharedPreviewStream()
      .then((stream) => {
        if (cancelled) return
        streamRef.current = stream
        const el = videoRef.current ?? videoEl
        if (el) {
          el.srcObject = stream
          const play = () => {
            el.onloadedmetadata = null
            void el.play().catch(() => {})
          }
          if (el.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
            play()
          } else {
            el.onloadedmetadata = play
          }
        }
      })
      .catch(() => {
        if (!cancelled) {
          toast.warning('Camera unavailable — your video preview is disabled')
        }
      })

    return () => {
      cancelled = true
      streamRef.current = null
      if (videoEl) videoEl.onloadedmetadata = null
      releaseSharedPreviewStream()
    }
  }, [enabled])

  if (!enabled) return null

  const isPip = variant === 'pip'

  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-lg border-2 bg-black shadow-lg',
        isRecording ? 'border-red-500' : 'border-background',
        isPip && 'absolute bottom-3 right-3 z-20',
        variant === 'standalone' && 'h-full w-full',
        className,
      )}
    >
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        aria-label='Your camera preview'
        className={cn(
          'h-full w-full object-cover [transform:translateZ(0)_scaleX(-1)]',
          variant === 'standalone' && 'aspect-video',
        )}
      />
      <span
        className={cn(
          'absolute rounded bg-black/60 px-1.5 py-0.5 text-[10px] font-medium text-white',
          isPip ? 'bottom-1 left-1.5' : 'bottom-2 left-2',
        )}
      >
        You
      </span>
      {isRecording && (
        <span className='absolute right-1.5 top-1.5 flex items-center gap-1 rounded bg-red-600/90 px-1.5 py-0.5 text-[10px] font-medium text-white'>
          <span className='size-1.5 animate-pulse rounded-full bg-white' />
          REC
        </span>
      )}
    </div>
  )
}
