import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

type MetricProps = {
  icon?: LucideIcon
  label: string
  value: string
  className?: string
}

export function Metric({ icon: Icon, label, value, className }: MetricProps) {
  return (
    <div className={cn('flex min-w-0 items-start gap-3', className)}>
      {Icon && (
        <div className='mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted'>
          <Icon className='size-3.5 text-muted-foreground' />
        </div>
      )}
      <div className='min-w-0'>
        <p className='text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
          {label}
        </p>
        <p className='truncate text-sm font-medium tabular-nums text-foreground'>
          {value}
        </p>
      </div>
    </div>
  )
}
