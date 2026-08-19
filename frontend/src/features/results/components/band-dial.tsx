import type { CSSProperties } from 'react'
import { BAND_MAX, bandPercent, formatBand } from '../lib/band'
import { bandDescriptor, cefrLevel } from '../lib/cefr'
import { cn } from '@/lib/utils'

const SIZE = 160
const STROKE = 10
const RADIUS = 62
const SWEEP_DEG = 270
const START_DEG = 135
const TICK_COUNT = 9

type BandDialProps = {
  band: number | null | undefined
  label?: string
  className?: string
}

function polar(cx: number, cy: number, r: number, deg: number) {
  const rad = (deg * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

export function BandDial({
  band,
  label = 'Overall',
  className,
}: BandDialProps) {
  const pct = bandPercent(band)
  const cefr = cefrLevel(band)
  const descriptor = bandDescriptor(band)
  const cx = SIZE / 2
  const circumference = 2 * Math.PI * RADIUS
  const arcLen = (SWEEP_DEG / 360) * circumference
  const filled = arcLen * (1 - pct / 100)
  const aria =
    band == null
      ? `${label} band not available`
      : `${label} band ${formatBand(band)} out of ${BAND_MAX}${cefr ? `, CEFR ${cefr}` : ''}`

  return (
    <div
      className={cn('relative shrink-0', className)}
      style={{ width: SIZE, height: SIZE }}
      role='img'
      aria-label={aria}
    >
      <svg
        className='absolute inset-0 size-full'
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        aria-hidden
      >
        <defs>
          <linearGradient id='band-dial-stroke' x1='0%' y1='0%' x2='100%' y2='0%'>
            <stop offset='0%' stopColor='var(--primary)' stopOpacity='0.55' />
            <stop offset='100%' stopColor='var(--primary)' />
          </linearGradient>
        </defs>
        {Array.from({ length: TICK_COUNT + 1 }, (_, i) => {
          const deg = START_DEG + (SWEEP_DEG * i) / TICK_COUNT
          const outer = polar(cx, cx, RADIUS + 6, deg)
          const inner = polar(cx, cx, RADIUS - 2, deg)
          return (
            <line
              key={i}
              x1={inner.x}
              y1={inner.y}
              x2={outer.x}
              y2={outer.y}
              className='stroke-muted-foreground/35'
              strokeWidth={i % 3 === 0 ? 1.5 : 1}
            />
          )
        })}
        <circle
          cx={cx}
          cy={cx}
          r={RADIUS}
          fill='none'
          className='stroke-muted'
          strokeWidth={STROKE}
          strokeLinecap='round'
          transform={`rotate(${START_DEG} ${cx} ${cx})`}
          strokeDasharray={`${arcLen} ${circumference}`}
        />
        <circle
          cx={cx}
          cy={cx}
          r={RADIUS}
          fill='none'
          stroke='url(#band-dial-stroke)'
          strokeWidth={STROKE}
          strokeLinecap='round'
          transform={`rotate(${START_DEG} ${cx} ${cx})`}
          strokeDasharray={`${arcLen} ${circumference}`}
          strokeDashoffset={filled}
          className='motion-safe:animate-[band-dial-reveal_700ms_ease-out_forwards] motion-reduce:transition-none'
          style={
            {
              '--dial-from': String(arcLen),
              '--dial-to': String(filled),
            } as CSSProperties
          }
        />
      </svg>
      <div className='relative flex size-full flex-col items-center justify-center pt-1'>
        <span className='text-5xl font-semibold tracking-tight tabular-nums text-foreground'>
          {formatBand(band)}
        </span>
        <span className='text-[10px] font-medium tracking-wider text-muted-foreground uppercase'>
          {label}
        </span>
        {cefr && (
          <span className='mt-1 rounded-full bg-primary/8 px-2 py-0.5 text-[10px] font-semibold tracking-wide text-primary'>
            {cefr}
            {descriptor ? ` · ${descriptor}` : ''}
          </span>
        )}
      </div>
    </div>
  )
}
