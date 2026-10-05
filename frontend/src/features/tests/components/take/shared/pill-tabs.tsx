import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

type PillTabItem = {
  label: string
  icon?: ReactNode
  badge?: ReactNode
}

type Props = {
  items: PillTabItem[]
  active: number
  onChange: (index: number) => void
  className?: string
}

export function PillTabs({ items, active, onChange, className }: Props) {
  return (
    <div
      role='tablist'
      className={cn('inline-flex rounded-lg bg-muted p-1', className)}
    >
      {items.map((it, i) => (
        <button
          key={i}
          type='button'
          role='tab'
          aria-selected={i === active}
          onClick={() => onChange(i)}
          className={cn(
            'flex min-h-9 items-center justify-center gap-1.5 rounded-md px-4 py-[7px] text-[13px] font-medium transition-all',
            i === active
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground',
          )}
        >
          {it.icon}
          <span>{it.label}</span>
          {it.badge}
        </button>
      ))}
    </div>
  )
}
