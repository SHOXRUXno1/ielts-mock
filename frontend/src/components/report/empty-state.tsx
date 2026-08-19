import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { Panel } from './panel'

type EmptyStateProps = {
  icon?: LucideIcon
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <Panel
      tone='flat'
      className={cn(
        'flex flex-col items-center justify-center gap-3 border-dashed bg-muted/20 py-16 text-center',
        className,
      )}
    >
      {Icon && (
        <div className='flex size-14 items-center justify-center rounded-2xl bg-muted'>
          <Icon className='size-7 text-muted-foreground' />
        </div>
      )}
      <p className='text-base font-medium text-foreground'>{title}</p>
      {description && (
        <p className='max-w-sm text-sm text-muted-foreground'>{description}</p>
      )}
      {action}
    </Panel>
  )
}
