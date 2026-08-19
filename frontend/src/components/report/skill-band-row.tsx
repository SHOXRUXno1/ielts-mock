import { cn } from '@/lib/utils'
import { formatBand } from '@/features/results/lib/band'
import { cefrLevel } from '@/features/results/lib/cefr'
import { SKILL_META, type SkillKey } from '@/features/results/lib/skill'
import { BandScale } from './band-scale'

type SkillBandRowProps = {
  skill: SkillKey
  band: number | null | undefined
  caption?: string
  className?: string
}

export function SkillBandRow({
  skill,
  band,
  caption,
  className,
}: SkillBandRowProps) {
  const meta = SKILL_META[skill]
  const Icon = meta.icon
  const cefr = cefrLevel(band)
  const empty = band == null

  return (
    <div
      className={cn(
        'grid items-center gap-3 rounded-xl px-2 py-3 sm:grid-cols-[9.5rem_minmax(0,1fr)_auto]',
        className,
      )}
    >
      <div className='flex min-w-0 items-center gap-3'>
        <div
          className={cn(
            'flex size-9 shrink-0 items-center justify-center rounded-lg',
            meta.surface,
          )}
        >
          <Icon className={cn('size-4', meta.accent)} />
        </div>
        <div className='min-w-0'>
          <p className='text-sm font-medium text-foreground'>{meta.label}</p>
          {caption && (
            <p className='text-xs tabular-nums text-muted-foreground'>{caption}</p>
          )}
        </div>
      </div>

      <div className='min-w-0'>
        {empty ? (
          <p className='text-sm text-muted-foreground'>Not attempted</p>
        ) : (
          <BandScale band={band} label={meta.label} barClass={meta.bar} />
        )}
      </div>

      <div className='flex items-center justify-end gap-2'>
        {!empty && (
          <>
            <span className='font-manrope text-lg font-semibold tracking-tight tabular-nums text-foreground'>
              {formatBand(band)}
            </span>
            {cefr && (
              <span className='hidden text-xs font-medium text-muted-foreground sm:inline'>
                {cefr}
              </span>
            )}
          </>
        )}
      </div>
    </div>
  )
}
