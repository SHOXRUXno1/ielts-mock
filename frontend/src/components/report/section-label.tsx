import type { ComponentProps } from 'react'
import { cn } from '@/lib/utils'

export function SectionLabel({
  className,
  ...props
}: ComponentProps<'p'>) {
  return (
    <p
      className={cn(
        'text-xs font-medium tracking-wider text-muted-foreground uppercase',
        className,
      )}
      {...props}
    />
  )
}
