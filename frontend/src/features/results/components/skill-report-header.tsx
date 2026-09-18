import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { ENTER } from '../lib/motion'
import { type SkillKey, skillMeta } from '../lib/skill'
import { BandValue, Panel } from '@/components/report'

type SkillReportHeaderProps = {
  skill: SkillKey
  band: number | null | undefined
  extra?: ReactNode
  status?: ReactNode
  action?: ReactNode
  className?: string
  variant?: 'default' | 'feature'
}

export function SkillReportHeader({
  skill,
  band,
  extra,
  status,
  action,
  className,
  variant = 'default',
}: SkillReportHeaderProps) {
  const meta = skillMeta(skill)
  const Icon = meta.icon

  if (variant === 'feature') {
    return (
      <Panel
        padding='none'
        className={cn('overflow-hidden', ENTER, className)}
      >
        <div className={cn('flex flex-wrap items-center justify-between gap-5 p-5 sm:p-7', meta.surface)}>
          <div className='flex min-w-0 items-center gap-4'>
            <div className='flex size-12 shrink-0 items-center justify-center rounded-2xl bg-background/80 shadow-sm'>
              <Icon className={cn('size-6', meta.accent)} />
            </div>
            <div>
              <p className={cn('text-xs font-semibold tracking-[0.16em] uppercase', meta.accent)}>
                IELTS {meta.label}
              </p>
              <h2 className='mt-1 font-manrope text-xl font-semibold tracking-tight text-foreground'>
                Your performance report
              </h2>
              {extra}
            </div>
          </div>
          <div className='flex items-center gap-3'>
            <div className='rounded-2xl bg-background/85 px-5 py-3 text-right shadow-sm ring-1 ring-black/5'>
              <p className='text-[10px] font-semibold tracking-[0.14em] text-muted-foreground uppercase'>Overall band</p>
              <BandValue band={band} label='' size='display' showCefr={false} showDescriptor={false} className={meta.accent} />
            </div>
            {action}
          </div>
        </div>
        {(status || band != null) && (
          <div className='flex flex-wrap items-center justify-between gap-3 border-t bg-card px-5 py-3 sm:px-7'>
            <p className='text-sm text-muted-foreground'>Read your score first, then use the feedback below to guide your next practice.</p>
            <div className='flex items-center gap-2'>
              <BandValue band={band} label='' size='sm' showDescriptor showCefr />
              {status}
            </div>
          </div>
        )}
      </Panel>
    )
  }

  return (
    <Panel padding='sm' className={cn(ENTER, className)}>
      <div className='flex flex-wrap items-center justify-between gap-4'>
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
            <p className='text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
              {meta.label}
            </p>
            <div className='flex flex-wrap items-center gap-2'>
              <BandValue
                band={band}
                label={meta.label}
                size='lg'
                showCefr
                showDescriptor
              />
              {status}
            </div>
            {extra}
          </div>
        </div>
        {action}
      </div>
    </Panel>
  )
}
