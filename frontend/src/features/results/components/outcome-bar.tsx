import { cn } from '@/lib/utils'

type OutcomeBarProps = {
  correct: number
  incorrect: number
  skipped: number
  showLegend?: boolean
  className?: string
}

export function OutcomeBar({
  correct,
  incorrect,
  skipped,
  showLegend = false,
  className,
}: OutcomeBarProps) {
  const total = correct + incorrect + skipped
  if (total === 0) return null

  return (
    <div className={cn('space-y-2', className)}>
      <div
        className='flex h-2 overflow-hidden rounded-full bg-muted'
        role='img'
        aria-label={`${correct} correct, ${incorrect} incorrect, ${skipped} skipped`}
      >
        {correct > 0 && (
          <div
            className='bg-success-foreground'
            style={{ width: `${(correct / total) * 100}%` }}
          />
        )}
        {incorrect > 0 && (
          <div
            className='bg-destructive'
            style={{ width: `${(incorrect / total) * 100}%` }}
          />
        )}
        {skipped > 0 && (
          <div
            className='bg-warning-foreground'
            style={{ width: `${(skipped / total) * 100}%` }}
          />
        )}
      </div>
      {showLegend && (
        <div className='flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-muted-foreground'>
          <LegendSwatch className='bg-success-foreground' label='Correct' count={correct} />
          <LegendSwatch className='bg-destructive' label='Incorrect' count={incorrect} />
          <LegendSwatch className='bg-warning-foreground' label='Skipped' count={skipped} />
        </div>
      )}
    </div>
  )
}

function LegendSwatch({
  className,
  label,
  count,
}: {
  className: string
  label: string
  count: number
}) {
  return (
    <span className='inline-flex items-center gap-1.5'>
      <span className={cn('size-1.5 rounded-full', className)} />
      {label}
      <span className='tabular-nums opacity-80'>{count}</span>
    </span>
  )
}
