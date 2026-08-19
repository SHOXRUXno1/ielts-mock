import type { AttemptDetailRead } from '@/lib/api/attempts'
import { cn } from '@/lib/utils'
import { bandPercent, formatBand } from '../lib/band'
import { SKILL_KEYS, SKILL_META } from '../lib/skill'
import { BandMeter } from './band-meter'

type BandBreakdownProps = {
  attempt: AttemptDetailRead
}

const SKILL_BAND: Record<(typeof SKILL_KEYS)[number], keyof AttemptDetailRead> = {
  listening: 'listening_band',
  reading: 'reading_band',
  writing: 'writing_band',
  speaking: 'speaking_band',
}

export function BandBreakdown({ attempt }: BandBreakdownProps) {
  const overallPct = bandPercent(attempt.overall_band)

  return (
    <div className='rounded-2xl bg-card p-6 shadow-sm ring-1 ring-border'>
      <div className='flex flex-wrap items-baseline justify-between gap-2'>
        <h3 className='text-base font-semibold text-foreground'>Band breakdown</h3>
        <p className='text-sm tabular-nums text-muted-foreground'>
          Overall {formatBand(attempt.overall_band)}
        </p>
      </div>
      <div className='mt-5 space-y-4'>
        {SKILL_KEYS.map((key) => {
          const meta = SKILL_META[key]
          const band = attempt[SKILL_BAND[key]] as number | null
          return (
            <div key={key} className='space-y-1.5'>
              <div className='flex items-center justify-between gap-3 text-sm'>
                <span className='font-medium text-foreground'>{meta.label}</span>
                <span className='tabular-nums text-muted-foreground'>
                  {formatBand(band)}
                </span>
              </div>
              <div className='relative'>
                <BandMeter
                  variant='linear'
                  band={band}
                  label={meta.label}
                  barClass={meta.bar}
                  showTicks
                />
                {attempt.overall_band != null && (
                  <div
                    className={cn(
                      'pointer-events-none absolute top-0 h-1.5 w-px -translate-x-1/2 border-l border-dashed border-foreground/40',
                    )}
                    style={{ left: `${overallPct}%` }}
                    aria-hidden
                  />
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
