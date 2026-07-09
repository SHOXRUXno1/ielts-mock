import { useCallback, useEffect, useRef, useState } from 'react'
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Circle,
  Loader2,
  Mic,
  MicOff,
  RotateCcw,
  Square,
} from 'lucide-react'
import { toast } from 'sonner'
import { audioPlaybackUrl, uploadAudio } from '@/lib/api/attempts'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import type { Question } from '../../data/schema'

type Props = {
  questions: Question[]
  answers: Record<string, Record<string, unknown>>
  onAnswer: (questionId: string, response: Record<string, unknown>) => void
}

type PartStatus = 'idle' | 'prep' | 'recording' | 'uploading' | 'recorded'

const PREP_SECONDS = 60
const PART2_MAX_RECORD_SECONDS = 120

function checkMicSync(): boolean | null {
  if (!navigator.mediaDevices?.getUserMedia) return false
  return null
}

function useMicCheck() {
  const [available, setAvailable] = useState<boolean | null>(checkMicSync)
  const checked = useRef(false)

  useEffect(() => {
    if (checked.current || available === false) return
    checked.current = true
    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        stream.getTracks().forEach((t) => t.stop())
        setAvailable(true)
      })
      .catch(() => setAvailable(false))
  }, [available])

  return available
}

export function SpeakingSection({ questions, answers, onAnswer }: Props) {
  const sorted = [...questions].sort((a, b) => a.order - b.order)
  const [currentStep, setCurrentStep] = useState(0)
  const micAvailable = useMicCheck()

  if (sorted.length === 0) {
    return (
      <p className='py-4 text-sm text-muted-foreground'>
        No speaking parts added to this section yet.
      </p>
    )
  }

  if (micAvailable === null) {
    return (
      <div className='flex items-center justify-center py-12'>
        <Loader2 className='size-6 animate-spin text-muted-foreground' />
        <span className='ml-2 text-sm text-muted-foreground'>
          Checking microphone access...
        </span>
      </div>
    )
  }

  if (micAvailable === false) {
    return (
      <Alert variant='destructive' className='my-4'>
        <MicOff className='size-4' />
        <AlertDescription>
          Microphone access is required for the Speaking section. Please allow
          microphone permissions in your browser settings and reload the page.
        </AlertDescription>
      </Alert>
    )
  }

  const current = sorted[currentStep]
  const recordedCount = sorted.filter(
    (q) => !!(answers[q.id] as Record<string, unknown> | undefined)?.audio_url
  ).length

  return (
    <div className='py-4'>
      {/* Stepper header */}
      <div className='mb-4 flex items-center justify-between'>
        <div className='flex items-center gap-2'>
          {sorted.map((q, i) => {
            const hasAudio = !!(
              answers[q.id] as Record<string, unknown> | undefined
            )?.audio_url
            return (
              <button
                key={q.id}
                onClick={() => setCurrentStep(i)}
                className={`flex size-8 items-center justify-center rounded-full border text-xs font-medium transition-colors ${
                  i === currentStep
                    ? 'border-primary bg-primary text-primary-foreground'
                    : hasAudio
                      ? 'border-green-500 bg-green-500/10 text-green-700 dark:text-green-400'
                      : 'border-muted-foreground/30 text-muted-foreground'
                }`}
              >
                {hasAudio ? <CheckCircle2 className='size-4' /> : i + 1}
              </button>
            )
          })}
        </div>
        <Badge variant='outline' className='text-xs'>
          {recordedCount}/{sorted.length} recorded
        </Badge>
      </div>

      <Progress
        value={(recordedCount / sorted.length) * 100}
        className='mb-6 h-1'
      />

      {/* Current part — key forces remount when switching */}
      {current && (
        <SpeakingPartCard
          key={current.id}
          question={current}
          initialAudioUrl={
            (answers[current.id]?.audio_url as string | undefined) ?? null
          }
          onAnswer={(resp) => onAnswer(current.id, resp)}
        />
      )}

      {/* Navigation */}
      <div className='mt-6 flex items-center justify-between'>
        <Button
          variant='outline'
          size='sm'
          disabled={currentStep === 0}
          onClick={() => setCurrentStep((s) => s - 1)}
        >
          <ChevronLeft className='mr-1 size-4' />
          Previous Part
        </Button>
        <span className='text-xs text-muted-foreground'>
          Part {currentStep + 1} of {sorted.length}
        </span>
        <Button
          variant='outline'
          size='sm'
          disabled={currentStep === sorted.length - 1}
          onClick={() => setCurrentStep((s) => s + 1)}
        >
          Next Part
          <ChevronRight className='ml-1 size-4' />
        </Button>
      </div>
    </div>
  )
}

function SpeakingPartCard({
  question,
  initialAudioUrl,
  onAnswer,
}: {
  question: Question
  initialAudioUrl: string | null
  onAnswer: (response: Record<string, unknown>) => void
}) {
  const content = question.content
  const part = (content.part as number) ?? 1
  const questionsList = (content.questions as string[]) ?? []
  const cueCard = content.cue_card as string | undefined
  const isPart2 = part === 2

  const [status, setStatus] = useState<PartStatus>(
    initialAudioUrl ? 'recorded' : 'idle'
  )
  const [audioUrl, setAudioUrl] = useState<string | null>(initialAudioUrl)
  const [elapsed, setElapsed] = useState(0)
  const [prepLeft, setPrepLeft] = useState(PREP_SECONDS)
  const [volume, setVolume] = useState(0)

  const mediaRecorder = useRef<MediaRecorder | null>(null)
  const chunks = useRef<Blob[]>([])
  const audioCtx = useRef<AudioContext | null>(null)
  const animFrame = useRef<number>(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const prepTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const stopRef = useRef<() => void>(() => {})

  const cleanup = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    if (prepTimerRef.current) {
      clearInterval(prepTimerRef.current)
      prepTimerRef.current = null
    }
    if (animFrame.current) {
      cancelAnimationFrame(animFrame.current)
      animFrame.current = 0
    }
    if (audioCtx.current) {
      audioCtx.current.close().catch(() => {})
      audioCtx.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
  }, [])

  useEffect(() => {
    return cleanup
  }, [cleanup])

  const startVolumeMonitor = useCallback((stream: MediaStream) => {
    const ctx = new AudioContext()
    const source = ctx.createMediaStreamSource(stream)
    const node = ctx.createAnalyser()
    node.fftSize = 256
    source.connect(node)
    audioCtx.current = ctx

    const dataArray = new Uint8Array(node.frequencyBinCount)
    const tick = () => {
      node.getByteFrequencyData(dataArray)
      const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length
      setVolume(Math.min(avg / 128, 1))
      animFrame.current = requestAnimationFrame(tick)
    }
    tick()
  }, [])

  const stopRecording = useCallback(() => {
    if (mediaRecorder.current?.state === 'recording') {
      mediaRecorder.current.stop()
    }
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [])

  useEffect(() => {
    stopRef.current = stopRecording
  }, [stopRecording])

  const doStartRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      chunks.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.current.push(e.data)
      }

      recorder.onstop = async () => {
        cleanup()
        const blob = new Blob(chunks.current, { type: 'audio/webm' })

        setStatus('uploading')
        let retries = 0
        const maxRetries = 3
        while (retries < maxRetries) {
          try {
            const url = await uploadAudio(blob)
            onAnswer({ audio_url: url })
            setAudioUrl(url)
            setStatus('recorded')
            toast.success(`Part ${part} recording saved`)
            return
          } catch (err) {
            retries++
            if (retries >= maxRetries) {
              const msg =
                err instanceof Error ? err.message : 'Unknown error'
              toast.error(
                `Upload failed after ${maxRetries} attempts: ${msg}`
              )
              setStatus('idle')
              return
            }
            await new Promise((r) => setTimeout(r, 1000 * retries))
          }
        }
      }

      mediaRecorder.current = recorder
      recorder.start()
      setStatus('recording')
      setElapsed(0)

      startVolumeMonitor(stream)

      timerRef.current = setInterval(() => {
        setElapsed((prev) => {
          const next = prev + 1
          if (isPart2 && next >= PART2_MAX_RECORD_SECONDS) {
            stopRef.current()
            toast.info('Part 2 time limit reached (2 minutes)')
          }
          return next
        })
      }, 1000)
    } catch {
      toast.error('Could not access microphone')
    }
  }, [part, isPart2, onAnswer, cleanup, startVolumeMonitor])

  const startPrep = useCallback(() => {
    setStatus('prep')
    setPrepLeft(PREP_SECONDS)
    prepTimerRef.current = setInterval(() => {
      setPrepLeft((prev) => {
        if (prev <= 1) {
          if (prepTimerRef.current) clearInterval(prepTimerRef.current)
          doStartRecording()
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }, [doStartRecording])

  const skipPrep = useCallback(() => {
    if (prepTimerRef.current) {
      clearInterval(prepTimerRef.current)
      prepTimerRef.current = null
    }
    doStartRecording()
  }, [doStartRecording])

  const handleReRecord = useCallback(() => {
    onAnswer({})
    setAudioUrl(null)
    setStatus('idle')
    setElapsed(0)
  }, [onAnswer])

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  return (
    <Card>
      <CardHeader>
        <div className='flex items-center justify-between'>
          <CardTitle className='flex items-center gap-2'>
            Part {part}
            <PartStatusBadge status={status} />
          </CardTitle>
          {isPart2 && status === 'recording' && (
            <span className='font-mono text-sm text-muted-foreground'>
              {formatTime(PART2_MAX_RECORD_SECONDS - elapsed)} left
            </span>
          )}
          {!isPart2 && status === 'recording' && (
            <span className='font-mono text-sm text-muted-foreground'>
              {formatTime(elapsed)}
            </span>
          )}
        </div>
        {isPart2 && (
          <CardDescription>
            You will have 1 minute to prepare, then 2 minutes to speak.
          </CardDescription>
        )}
      </CardHeader>

      <CardContent className='space-y-4'>
        {/* Cue card */}
        {cueCard && (
          <div className='rounded-lg border-2 border-amber-500/30 bg-amber-50/50 p-4 dark:bg-amber-950/20'>
            <p className='mb-2 text-xs font-semibold uppercase tracking-wider text-amber-700 dark:text-amber-400'>
              Cue Card
            </p>
            <p className='whitespace-pre-wrap text-sm leading-relaxed'>
              {cueCard}
            </p>
          </div>
        )}

        {/* Questions list */}
        {questionsList.length > 0 && (
          <div className='space-y-2'>
            {questionsList.map((q, i) => (
              <p key={i} className='text-sm leading-relaxed'>
                <span className='mr-2 inline-flex size-5 items-center justify-center rounded-full bg-muted text-xs font-medium'>
                  {i + 1}
                </span>
                {q}
              </p>
            ))}
          </div>
        )}

        {/* Prep countdown (Part 2) */}
        {status === 'prep' && (
          <div className='flex flex-col items-center gap-3 rounded-lg border bg-muted/50 py-6'>
            <div className='text-4xl font-bold tabular-nums'>
              {formatTime(prepLeft)}
            </div>
            <p className='text-sm text-muted-foreground'>
              Preparation time remaining
            </p>
            <Progress
              value={((PREP_SECONDS - prepLeft) / PREP_SECONDS) * 100}
              className='mx-auto h-1.5 w-48'
            />
            <Button size='sm' variant='secondary' onClick={skipPrep}>
              Start speaking now
            </Button>
          </div>
        )}

        {/* Recording indicator */}
        {status === 'recording' && (
          <div className='flex flex-col items-center gap-3 rounded-lg border border-red-500/20 bg-red-50/50 py-6 dark:bg-red-950/20'>
            <div className='flex items-center gap-2'>
              <span className='relative flex size-3'>
                <span className='absolute inline-flex size-full animate-ping rounded-full bg-red-400 opacity-75' />
                <span className='relative inline-flex size-3 rounded-full bg-red-500' />
              </span>
              <span className='text-sm font-medium text-red-700 dark:text-red-400'>
                Recording
              </span>
            </div>

            {/* Volume meter */}
            <div className='flex h-8 w-48 items-end justify-center gap-0.5'>
              {Array.from({ length: 20 }).map((_, i) => (
                <div
                  key={i}
                  className='w-1.5 rounded-t transition-all duration-75'
                  style={{
                    height: `${Math.max(4, volume * 32 * Math.sin(((i + 1) / 20) * Math.PI))}px`,
                    backgroundColor:
                      volume * 20 > i
                        ? i > 15
                          ? '#ef4444'
                          : i > 10
                            ? '#f59e0b'
                            : '#22c55e'
                        : '#e5e7eb',
                  }}
                />
              ))}
            </div>

            {isPart2 && (
              <Progress
                value={(elapsed / PART2_MAX_RECORD_SECONDS) * 100}
                className='mx-auto h-1.5 w-48'
              />
            )}
          </div>
        )}

        {/* Uploading indicator */}
        {status === 'uploading' && (
          <div className='flex items-center justify-center gap-2 py-4'>
            <Loader2 className='size-5 animate-spin text-primary' />
            <span className='text-sm text-muted-foreground'>
              Uploading recording...
            </span>
          </div>
        )}

        {/* Recorded preview */}
        {status === 'recorded' && audioUrl && (
          <div className='flex items-center gap-3 rounded-lg border bg-green-50/50 p-3 dark:bg-green-950/20'>
            <CheckCircle2 className='size-5 shrink-0 text-green-600' />
            <audio
              controls
              src={audioPlaybackUrl(audioUrl)}
              className='h-8 flex-1'
            />
          </div>
        )}

        {/* Action buttons */}
        <div className='flex items-center gap-2'>
          {status === 'idle' && (
            <Button onClick={isPart2 ? startPrep : doStartRecording}>
              <Mic className='mr-1 size-4' />
              {isPart2 ? 'Start Preparation' : 'Start Recording'}
            </Button>
          )}

          {status === 'recording' && (
            <Button variant='destructive' onClick={stopRecording}>
              <Square className='mr-1 size-4' />
              Stop Recording
            </Button>
          )}

          {status === 'recorded' && (
            <Button variant='outline' size='sm' onClick={handleReRecord}>
              <RotateCcw className='mr-1 size-4' />
              Re-record
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function PartStatusBadge({ status }: { status: PartStatus }) {
  switch (status) {
    case 'idle':
      return (
        <Badge variant='outline' className='text-xs'>
          <Circle className='mr-1 size-2' />
          Not started
        </Badge>
      )
    case 'prep':
      return (
        <Badge variant='secondary' className='text-xs'>
          Preparing
        </Badge>
      )
    case 'recording':
      return (
        <Badge variant='destructive' className='text-xs'>
          <span className='mr-1 inline-block size-1.5 animate-pulse rounded-full bg-white' />
          Recording
        </Badge>
      )
    case 'uploading':
      return (
        <Badge variant='secondary' className='text-xs'>
          <Loader2 className='mr-1 size-3 animate-spin' />
          Uploading
        </Badge>
      )
    case 'recorded':
      return (
        <Badge className='bg-green-600 text-xs hover:bg-green-700'>
          <CheckCircle2 className='mr-1 size-3' />
          Recorded
        </Badge>
      )
  }
}
