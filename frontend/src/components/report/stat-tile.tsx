import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

type StatTileProps = {
  icon: LucideIcon
  label: string
  value: string | number
  className?: string
}

export function StatTile({ icon: Icon, label, value, className }: StatTileProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-4 rounded-2xl border border-border/60 bg-card p-4 shadow-sm',
        className,
      )}
    >
      <div className='flex size-10 shrink-0 items-center justify-center rounded-xl bg-muted'>
        <Icon className='size-4 text-muted-foreground' />
      </div>
      <div className='min-w-0'>
        <p className='font-manrope text-2xl font-semibold tracking-tight tabular-nums text-foreground'>
          {value}
        </p>
        <p className='text-xs text-muted-foreground'>{label}</p>
      </div>
    </div>
  )
}
