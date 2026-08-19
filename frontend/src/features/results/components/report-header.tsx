import type { ReactNode } from 'react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { formatBand } from '../lib/band'
import { bandDescriptor, cefrLevel } from '../lib/cefr'
import { type SkillKey, skillMeta } from '../lib/skill'

type ReportHeaderProps = {
  skill: SkillKey
  band: number | null | undefined
  extra?: ReactNode
  status?: ReactNode
  action?: ReactNode
  className?: string
}

export function ReportHeader({
  skill,
  band,
  extra,
  status,
  action,
  className,
}: ReportHeaderProps) {
  const meta = skillMeta(skill)
  const Icon = meta.icon
  const descriptor = bandDescriptor(band)
  const cefr = cefrLevel(band)

  return (
    <div
      className={cn(
        'flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-card p-5 shadow-sm ring-1 ring-border',
        className,
      )}
    >
      <div className='flex min-w-0 items-center gap-3'>
        <div
          className={cn(
            'flex size-10 items-center justify-center rounded-xl',
            meta.surface,
          )}
        >
          <Icon className={cn('size-5', meta.accent)} />
        </div>
        <div className='min-w-0'>
          <p className='text-[10px] font-medium tracking-wider text-muted-foreground uppercase'>
            {meta.label}
          </p>
          <div className='flex flex-wrap items-baseline gap-2'>
            <p className='text-3xl font-semibold tracking-tight tabular-nums text-foreground'>
              {formatBand(band)}
            </p>
            {descriptor && (
              <span className='text-sm text-muted-foreground'>{descriptor}</span>
            )}
            {cefr && (
              <Badge variant='outline' className='rounded-md text-[10px]'>
                {cefr}
              </Badge>
            )}
            {status}
          </div>
          {extra}
        </div>
      </div>
      {action}
    </div>
  )
}
