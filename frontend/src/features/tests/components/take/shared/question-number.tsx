import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

type Props = {
  children: ReactNode
  variant?: 'chip' | 'inline'
  className?: string
}

export function QuestionNumber({ children, variant = 'chip', className }: Props) {
  return (
    <span
      data-q-chip
      className={cn(
        variant === 'chip'
          ? 'inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-slate-100 text-[11px] font-bold text-slate-600'
          : 'text-[13px] font-medium text-blue-600',
        className,
      )}
    >
      {children}
    </span>
  )
}
