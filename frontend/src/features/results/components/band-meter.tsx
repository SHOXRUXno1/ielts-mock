import { cn } from '@/lib/utils'
import { BAND_MAX, bandPercent, formatBand } from '../lib/band'

type BandMeterProps = {
  band: number | null | undefined
  variant?: 'radial' | 'linear'
  strokeClass?: string
  barClass?: string
  size?: number
  label?: string
  className?: string
  showTicks?: boolean
}

export function BandMeter({
  band,
  variant = 'linear',
  strokeClass = 'stroke-primary',
  barClass = 'bg-primary',
  size = 112,
  label = 'Overall',
  className,
  showTicks = false,
}: BandMeterProps) {
  const pct = bandPercent(band)
  const valueLabel = `${formatBand(band)} out of ${BAND_MAX}`
  const empty = band == null

  if (variant === 'linear') {
    return (
      <div className={cn('w-full', className)}>
        <div
          className={cn(
            'h-1.5 w-full overflow-hidden rounded-full',
            empty ? 'track-hatched bg-muted/60' : 'bg-muted',
          )}
          role='meter'
          aria-label={label}
          aria-valuemin={0}
          aria-valuemax={BAND_MAX}
          aria-valuenow={band ?? undefined}
          aria-valuetext={valueLabel}
        >
          {!empty && (
            <div
              className={cn(
                'h-full rounded-full transition-all duration-200 motion-reduce:transition-none',
                barClass,
              )}
              style={{ width: `${pct}%` }}
            />
          )}
        </div>
        {showTicks && (
          <div className='mt-1 flex justify-between text-[10px] tabular-nums text-muted-foreground'>
            <span>0</span>
            <span>4.5</span>
            <span>9</span>
          </div>
        )}
      </div>
    )
  }

  const r = 48
  const c = 2 * Math.PI * r
  const dash = (pct / 100) * c
  const cx = size / 2

  return (
    <div
      className={cn('relative shrink-0', className)}
      style={{ width: size, height: size }}
      role='img'
      aria-label={`${label} band ${valueLabel}`}
    >
      <svg
        className='absolute inset-0 size-full -rotate-90'
        viewBox={`0 0 ${size} ${size}`}
        aria-hidden
      >
        <circle
          cx={cx}
          cy={cx}
          r={r}
          fill='none'
          className='stroke-muted'
          strokeWidth='7'
        />
        <circle
          cx={cx}
          cy={cx}
          r={r}
          fill='none'
          className={cn('transition-all duration-200', strokeClass)}
          strokeWidth='7'
          strokeLinecap='round'
          strokeDasharray={`${dash} ${c}`}
        />
      </svg>
      <div className='relative flex size-full flex-col items-center justify-center'>
        <span className='text-2xl font-semibold tracking-tight tabular-nums text-foreground'>
          {formatBand(band)}
        </span>
        <span className='text-[10px] font-medium tracking-wider text-muted-foreground uppercase'>
          {label}
        </span>
      </div>
    </div>
  )
}
