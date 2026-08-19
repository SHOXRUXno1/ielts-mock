import { cn } from '@/lib/utils'

type AnswerOutcomeBarProps = {
  correct: number
  incorrect: number
  skipped: number
  className?: string
}

export function AnswerOutcomeBar({
  correct,
  incorrect,
  skipped,
  className,
}: AnswerOutcomeBarProps) {
  const total = correct + incorrect + skipped
  if (total === 0) return null

  return (
    <div
      className={cn('flex h-2 overflow-hidden rounded-full bg-muted', className)}
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
  )
}
