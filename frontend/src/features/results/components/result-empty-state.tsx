import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { ENTER } from '../lib/motion'
import { Panel } from '@/components/report'

type ResultEmptyStateProps = {
  icon: LucideIcon
  title: string
  description: string
  action?: ReactNode
  className?: string
}

export function ResultEmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: ResultEmptyStateProps) {
  return (
    <Panel
      tone='flat'
      padding='md'
      className={cn(
        'border-dashed bg-surface-sunken',
        ENTER,
        className,
      )}
    >
      <div className='flex flex-col items-center justify-center gap-3 py-8 text-center'>
        <div className='flex size-12 items-center justify-center rounded-full bg-muted'>
          <Icon className='size-5 text-muted-foreground' />
        </div>
        <div className='space-y-1'>
          <h3 className='text-base font-semibold text-foreground'>{title}</h3>
          <p className='max-w-sm text-sm leading-relaxed text-muted-foreground'>
            {description}
          </p>
        </div>
        {action}
      </div>
    </Panel>
  )
}
