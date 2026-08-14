import { cn } from '@/lib/utils'

type Props = {
  count: number
  total: number
  className?: string
}

export function StatusBadge({ count, total, className }: Props) {
  const isComplete = count === total && total > 0

  return (
    <span
      className={cn(
        'rounded-full px-2 py-0.5 text-[11px] font-medium tabular-nums',
        isComplete
          ? 'bg-emerald-50 text-emerald-600'
          : 'bg-slate-100 text-slate-400',
        className,
      )}
    >
      {count}/{total}
    </span>
  )
}
