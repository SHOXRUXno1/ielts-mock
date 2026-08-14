import { cn } from '@/lib/utils'

type Variant = 'ok' | 'warn' | 'error' | 'neutral'

type Props = {
  current: number
  target: number
  className?: string
}

function resolveVariant(current: number, target: number): Variant {
  if (current === target) return 'ok'
  if (current === 0) return 'neutral'
  if (current > target) return 'warn'
  return 'warn'
}

const styles: Record<Variant, string> = {
  ok: 'bg-success/20 text-success-foreground',
  warn: 'bg-warning/20 text-warning-foreground',
  error: 'bg-destructive/10 text-destructive',
  neutral: 'bg-muted text-muted-foreground',
}

export function StatusChip({ current, target, className }: Props) {
  const variant = resolveVariant(current, target)
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] font-semibold tabular-nums',
        styles[variant],
        className,
      )}
    >
      {current}/{target}
    </span>
  )
}
