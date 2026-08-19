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
}

export function SkillReportHeader({
  skill,
  band,
  extra,
  status,
  action,
  className,
}: SkillReportHeaderProps) {
  const meta = skillMeta(skill)
  const Icon = meta.icon

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
