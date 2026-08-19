import { cn } from '@/lib/utils'
import { BAND_MAX, BAND_SEGMENT_COUNT, bandSegments, formatBand } from '../../lib/band'

type BandScaleProps = {
  band: number | null | undefined
  label?: string
  barClass?: string
  className?: string
  showTicks?: boolean
}

export function BandScale({
  band,
  label = 'Band',
  barClass = 'bg-primary',
  className,
  showTicks = false,
}: BandScaleProps) {
  const filled = bandSegments(band)
  const empty = band == null
  const valueLabel = `${formatBand(band)} out of ${BAND_MAX}`

  return (
    <div className={cn('w-full', className)}>
      <div
        className={cn(
          'flex h-1.5 w-full gap-0.5',
          empty && 'track-hatched rounded-full bg-muted/60',
        )}
        role='meter'
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={BAND_MAX}
        aria-valuenow={band ?? undefined}
        aria-valuetext={valueLabel}
      >
        {!empty &&
          Array.from({ length: BAND_SEGMENT_COUNT }, (_, i) => (
            <div
              key={i}
              className={cn(
                'h-full min-w-0 flex-1 rounded-[1px]',
                i < filled
                  ? cn(
                      barClass,
                      'motion-safe:animate-[band-scale-fill_400ms_ease-out_both]',
                    )
                  : 'bg-muted',
              )}
              style={
                i < filled ? { animationDelay: `${i * 16}ms` } : undefined
              }
            />
          ))}
      </div>
      {showTicks && (
        <div className='mt-1 flex justify-between text-[11px] tabular-nums text-muted-foreground'>
          <span>0</span>
          <span>4.5</span>
          <span>9</span>
        </div>
      )}
    </div>
  )
}
