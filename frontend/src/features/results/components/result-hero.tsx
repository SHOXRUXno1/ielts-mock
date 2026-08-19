import type { ReactNode } from 'react'
import { Clock, Flag, Play } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import type { AttemptDetailRead } from '@/lib/api/attempts'
import { formatBand } from '../lib/band'
import { SKILL_KEYS, SKILL_META } from '../lib/skill'
import { attemptStatusMeta, formatAttemptDate, formatAttemptDuration } from '../lib/status'
import { BandDial } from './band-dial'
import { BandMeter } from './band-meter'
import { StatItem } from './stat-item'

type ResultHeroProps = {
  attempt: AttemptDetailRead
  scoringActive: boolean
  actions?: ReactNode
}

const SKILL_BAND: Record<(typeof SKILL_KEYS)[number], keyof AttemptDetailRead> = {
  listening: 'listening_band',
  reading: 'reading_band',
  writing: 'writing_band',
  speaking: 'speaking_band',
}

export function ResultHero({ attempt, scoringActive, actions }: ResultHeroProps) {
  const status = attemptStatusMeta(attempt.status)
  const duration = formatAttemptDuration(attempt.started_at, attempt.finished_at)
  const overall =
    scoringActive && attempt.overall_band == null ? null : attempt.overall_band
  const dialLabel =
    scoringActive && attempt.overall_band == null ? 'Pending' : 'Overall'

  return (
    <div className='overflow-hidden rounded-2xl bg-card shadow-sm ring-1 ring-border'>
      <div className='relative bg-[radial-gradient(ellipse_at_top,color-mix(in_oklch,var(--primary)_6%,transparent),transparent_62%)]'>
        <div className='grid gap-6 px-6 py-6 lg:grid-cols-[auto_minmax(0,1fr)] lg:items-center'>
          <BandDial band={overall} label={dialLabel} />

          <div className='min-w-0 space-y-4'>
            <div className='flex flex-wrap items-center gap-2.5'>
              <h1 className='text-2xl font-semibold tracking-tight text-foreground'>
                {attempt.test_title ?? 'Test Result'}
              </h1>
              <Badge variant={status.variant} className='rounded-lg gap-1.5'>
                <span className={status.dot + ' size-1.5 rounded-full'} />
                {status.label}
              </Badge>
            </div>

            <div className='grid gap-3 sm:grid-cols-3'>
              <StatItem
                icon={Play}
                label='Started'
                value={formatAttemptDate(attempt.started_at)}
              />
              <StatItem
                icon={Flag}
                label='Finished'
                value={formatAttemptDate(attempt.finished_at)}
              />
              <StatItem
                icon={Clock}
                label='Duration'
                value={duration ?? '—'}
              />
            </div>

            {actions ? (
              <>
                <Separator />
                {actions}
              </>
            ) : null}
          </div>
        </div>
      </div>

      <div className='hidden border-t border-border bg-surface-raised/70 px-6 py-4 md:block'>
        <div className='grid grid-cols-4 gap-6'>
          {SKILL_KEYS.map((key) => {
            const meta = SKILL_META[key]
            const band = attempt[SKILL_BAND[key]] as number | null
            return (
              <div key={key} className='min-w-0'>
                <div className='mb-1.5 flex items-center justify-between gap-2 text-xs'>
                  <span className='font-medium text-foreground'>{meta.label}</span>
                  <span className='tabular-nums text-muted-foreground'>
                    {formatBand(band)}
                  </span>
                </div>
                <BandMeter
                  variant='linear'
                  band={band}
                  label={meta.label}
                  barClass={meta.bar}
                />
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
