import { useEffect, useState } from 'react'
import { Check, Loader2, PenLine, Mic, AlertCircle } from 'lucide-react'
import type { EvaluationJobRead } from '@/lib/api/attempts'
import { cn } from '@/lib/utils'

export type EvalPhase = 'queued' | 'scoring' | 'ready' | 'failed' | 'none'

export function jobPhase(jobs: EvaluationJobRead[]): EvalPhase {
  if (jobs.length === 0) return 'none'
  if (jobs.some((j) => j.status === 'processing')) return 'scoring'
  if (jobs.some((j) => j.status === 'pending')) return 'queued'
  if (jobs.every((j) => j.status === 'failed')) return 'failed'
  if (jobs.some((j) => j.status === 'done')) return 'ready'
  if (jobs.some((j) => j.status === 'failed')) return 'failed'
  return 'none'
}

export function isJobActive(jobs: EvaluationJobRead[]): boolean {
  const phase = jobPhase(jobs)
  return phase === 'queued' || phase === 'scoring'
}

export function showEvalProgress(jobs: EvaluationJobRead[]): boolean {
  const phase = jobPhase(jobs)
  return phase === 'queued' || phase === 'scoring' || phase === 'failed'
}

function formatElapsed(fromIso: string | null | undefined): string | null {
  if (!fromIso) return null
  const ms = Date.now() - new Date(fromIso).getTime()
  if (!Number.isFinite(ms) || ms < 0) return null
  const sec = Math.floor(ms / 1000)
  if (sec < 60) return `${sec}s`
  const min = Math.floor(sec / 60)
  const rem = sec % 60
  return rem === 0 ? `${min} min` : `${min} min ${rem}s`
}

function useElapsed(fromIso: string | null | undefined, active: boolean): string | null {
  const [, setTick] = useState(0)
  useEffect(() => {
    if (!active) return
    const id = window.setInterval(() => setTick((n) => n + 1), 1000)
    return () => window.clearInterval(id)
  }, [active])
  return active ? formatElapsed(fromIso) : null
}

const STEPS = ['Submitted', 'In queue', 'Scoring', 'Ready'] as const

function stepIndex(phase: EvalPhase): number {
  if (phase === 'ready') return 3
  if (phase === 'scoring') return 2
  if (phase === 'queued') return 1
  if (phase === 'failed') return 2
  return 0
}

type Copy = {
  title: string
  body: string
}

function copyFor(
  section: 'writing' | 'speaking',
  phase: EvalPhase,
  retryCount: number,
): Copy {
  const essay = section === 'writing'
  if (phase === 'queued' && retryCount > 0) {
    return {
      title: essay ? 'Retrying writing score' : 'Retrying speaking score',
      body: `The examiner was busy. Attempt ${retryCount + 1} of 3 — your answers are saved.`,
    }
  }
  if (phase === 'queued') {
    return {
      title: essay ? 'Writing is in the queue' : 'Speaking is in the queue',
      body: essay
        ? 'Listening and Reading are already scored. Your essay waits its turn. Usually 1–2 minutes; a few minutes if many students submitted together.'
        : 'Your recording is waiting to be transcribed and scored. Usually 1–2 minutes; longer if several students finished at once.',
    }
  }
  if (phase === 'scoring') {
    return {
      title: essay ? 'Scoring your writing' : 'Scoring your speaking',
      body: essay
        ? 'The examiner is reading your Task 1 and Task 2. This usually takes about a minute.'
        : 'Transcribing your recording, then scoring. This usually takes one to two minutes.',
    }
  }
  if (phase === 'failed') {
    return {
      title: essay
        ? 'Writing could not be scored automatically'
        : 'Speaking could not be scored automatically',
      body: 'Your answers were saved. A teacher can score this attempt. You can leave this page and come back later.',
    }
  }
  return {
    title: essay ? 'Writing scored' : 'Speaking scored',
    body: 'Your band is ready.',
  }
}

function IndeterminateBar({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'relative h-1.5 overflow-hidden rounded-full bg-muted',
        className,
      )}
      aria-hidden
    >
      <div className='absolute inset-y-0 w-1/3 rounded-full bg-violet-500 motion-safe:animate-[eval-indeterminate_1.4s_ease-in-out_infinite]' />
    </div>
  )
}

function Stepper({ current, failed }: { current: number; failed?: boolean }) {
  return (
    <ol className='flex items-center gap-0' aria-label='Scoring progress'>
      {STEPS.map((label, i) => {
        const done = i < current
        const active = i === current && !failed
        const isFail = failed && i === current
        return (
          <li key={label} className='flex min-w-0 flex-1 items-center'>
            <div className='flex min-w-0 flex-col items-center gap-1.5'>
              <span
                className={cn(
                  'flex size-6 items-center justify-center rounded-full text-[11px] font-semibold',
                  done && 'bg-emerald-500 text-white',
                  active && 'bg-violet-600 text-white',
                  isFail && 'bg-destructive text-white',
                  !done && !active && !isFail && 'bg-muted text-muted-foreground',
                )}
              >
                {done ? <Check className='size-3.5' strokeWidth={3} /> : i + 1}
              </span>
              <span
                className={cn(
                  'text-center text-[11px] leading-tight',
                  active || done ? 'font-medium text-foreground' : 'text-muted-foreground',
                )}
              >
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={cn(
                  'mb-5 h-px min-w-4 flex-1',
                  i < current ? 'bg-emerald-500' : 'bg-border',
                )}
              />
            )}
          </li>
        )
      })}
    </ol>
  )
}

export function EvaluationProgressCard({
  jobs,
  section,
  className,
}: {
  jobs: EvaluationJobRead[]
  section: 'writing' | 'speaking'
  className?: string
}) {
  const phase = jobPhase(jobs)
  const job = jobs[0]
  const retryCount = job?.retry_count ?? 0
  const elapsed = useElapsed(
    job?.created_at,
    phase === 'queued' || phase === 'scoring',
  )

  if (phase === 'none' || phase === 'ready') return null

  const copy = copyFor(section, phase, retryCount)
  const Icon = section === 'writing' ? PenLine : Mic
  const failed = phase === 'failed'

  return (
    <div
      className={cn(
        'rounded-2xl border bg-card p-5',
        failed ? 'border-destructive/30' : 'border-border',
        className,
      )}
      role='status'
      aria-live='polite'
    >
      <div className='flex items-start gap-3'>
        <div
          className={cn(
            'flex size-10 shrink-0 items-center justify-center rounded-xl',
            failed ? 'bg-destructive/10 text-destructive' : 'bg-violet-500/10 text-violet-600 dark:text-violet-400',
          )}
        >
          {failed ? (
            <AlertCircle className='size-5' />
          ) : phase === 'scoring' ? (
            <Loader2 className='size-5 animate-spin' />
          ) : (
            <Icon className='size-5' />
          )}
        </div>
        <div className='min-w-0 flex-1 space-y-1'>
          <div className='flex flex-wrap items-baseline gap-x-2 gap-y-0.5'>
            <h3 className='text-[15px] font-semibold text-foreground'>{copy.title}</h3>
            {elapsed && !failed && (
              <span className='text-xs tabular-nums text-muted-foreground'>
                {elapsed} elapsed
              </span>
            )}
          </div>
          <p className='text-sm leading-relaxed text-muted-foreground'>{copy.body}</p>
          {!failed && (
            <p className='text-xs text-muted-foreground'>This page updates automatically.</p>
          )}
        </div>
      </div>

      {!failed && <IndeterminateBar className='mt-4' />}

      <div className='mt-5'>
        <Stepper current={stepIndex(phase)} failed={failed} />
      </div>
    </div>
  )
}

export function SectionEvalBadge({
  jobs,
  emptyLabel = '—',
}: {
  jobs: EvaluationJobRead[]
  emptyLabel?: string
}) {
  const phase = jobPhase(jobs)
  if (phase === 'queued') {
    return (
      <p className='text-sm font-medium text-violet-600 dark:text-violet-400'>In queue</p>
    )
  }
  if (phase === 'scoring') {
    return (
      <p className='flex items-center gap-1.5 text-sm font-medium text-violet-600 dark:text-violet-400'>
        <Loader2 className='size-3.5 animate-spin' />
        Scoring…
      </p>
    )
  }
  if (phase === 'failed') {
    return <p className='text-sm font-medium text-destructive'>Needs review</p>
  }
  return <p className='text-3xl font-bold text-foreground'>{emptyLabel}</p>
}
