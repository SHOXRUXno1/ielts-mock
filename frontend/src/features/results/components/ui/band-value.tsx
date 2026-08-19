import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { BAND_MAX, formatBand } from '../../lib/band'
import { bandDescriptor, cefrLevel } from '../../lib/cefr'

type BandValueSize = 'display' | 'lg' | 'sm'

type BandValueProps = {
  band: number | null | undefined
  label?: string
  size?: BandValueSize
  showCefr?: boolean
  showDescriptor?: boolean
  className?: string
}

const SIZE_CLASS: Record<BandValueSize, string> = {
  display: 'text-6xl',
  lg: 'text-3xl',
  sm: 'text-xl',
}

export function BandValue({
  band,
  label = 'Overall',
  size = 'lg',
  showCefr = true,
  showDescriptor = true,
  className,
}: BandValueProps) {
  const cefr = cefrLevel(band)
  const descriptor = bandDescriptor(band)
  const aria =
    band == null
      ? `${label} band not available`
      : `${label} band ${formatBand(band)} out of ${BAND_MAX}${cefr ? `, CEFR ${cefr}` : ''}`

  return (
    <div className={cn('min-w-0', className)} role='img' aria-label={aria}>
      <p
        className={cn(
          'font-manrope font-semibold tracking-tight tabular-nums text-foreground',
          SIZE_CLASS[size],
        )}
      >
        {formatBand(band)}
      </p>
      {label && size === 'display' && (
        <p className='mt-1 text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
          {label}
        </p>
      )}
      {(showDescriptor || showCefr) && (descriptor || cefr) && (
        <div
          className={cn(
            'flex flex-wrap items-center gap-2',
            size === 'display' ? 'mt-2' : 'mt-1',
          )}
        >
          {showDescriptor && descriptor && (
            <span className='text-sm text-muted-foreground'>{descriptor}</span>
          )}
          {showCefr && cefr && (
            <Badge variant='outline' className='rounded-md text-[11px]'>
              {cefr}
            </Badge>
          )}
        </div>
      )}
    </div>
  )
}
