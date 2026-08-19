import { Link } from '@tanstack/react-router'
import { ChevronRight } from 'lucide-react'
import type { EvaluationJobRead } from '@/lib/api/attempts'
import { cn } from '@/lib/utils'
import { formatBand } from '../lib/band'
import { bandDescriptor } from '../lib/cefr'
import { type SkillKey, skillMeta } from '../lib/skill'
import { isSectionNotAttempted } from '../lib/status'
import { jobPhase, SectionEvalBadge } from '../evaluation-progress'
import { BandMeter } from './band-meter'

type SkillBandCardProps = {
  skill: SkillKey
  band: number | null
  raw?: number | null
  total?: number | null
  attemptStatus?: string
  evalJobs?: EvaluationJobRead[]
  index?: number
}

export function SkillBandCard({
  skill,
  band,
  raw,
  total,
  attemptStatus,
  evalJobs,
  index = 0,
}: SkillBandCardProps) {
  const meta = skillMeta(skill)
  const Icon = meta.icon
  const isNotAttempted = isSectionNotAttempted(band, attemptStatus)
  const evalPhase = evalJobs ? jobPhase(evalJobs) : 'none'
  const showEval =
    evalPhase === 'queued' || evalPhase === 'scoring' || evalPhase === 'failed'
  const descriptor = bandDescriptor(band)

  return (
    <Link
      to='.'
      search={(prev) => ({ ...prev, tab: skill })}
      replace
      className={cn(
        'group block rounded-2xl bg-card p-5 shadow-sm ring-1 ring-border transition-all duration-200',
        'hover:-translate-y-0.5 hover:shadow-md focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
        'motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2 motion-safe:duration-300',
      )}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className='mb-4 flex items-center justify-between gap-2'>
        <div className='flex items-center gap-2.5'>
          <div
            className={cn(
              'flex size-9 items-center justify-center rounded-lg',
              meta.surface,
            )}
          >
            <Icon className={cn('size-4', meta.accent)} />
          </div>
          <span className='text-sm font-medium text-foreground'>{meta.label}</span>
        </div>
        <ChevronRight className='size-4 text-muted-foreground opacity-0 transition-opacity duration-200 group-hover:opacity-100' />
      </div>
      {isNotAttempted && !showEval ? (
        <p className='text-sm text-muted-foreground'>Not attempted</p>
      ) : showEval ? (
        <SectionEvalBadge jobs={evalJobs ?? []} />
      ) : (
        <>
          <p className='text-4xl font-semibold tracking-tight tabular-nums text-foreground'>
            {formatBand(band)}
          </p>
          {descriptor && (
            <p className='mt-0.5 text-xs text-muted-foreground'>{descriptor}</p>
          )}
          <BandMeter
            variant='linear'
            band={band}
            label={meta.label}
            barClass={meta.bar}
            className='mt-3'
          />
        </>
      )}
      {!isNotAttempted && !showEval && raw != null && total != null && (
        <p className='mt-2 inline-flex rounded-md bg-muted px-1.5 py-0.5 text-[11px] tabular-nums text-muted-foreground'>
          {raw}/{total} correct
        </p>
      )}
    </Link>
  )
}
