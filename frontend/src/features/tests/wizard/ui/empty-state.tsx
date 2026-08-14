import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

type Props = {
  icon: LucideIcon
  headline: string
  description?: string
  action?: ReactNode
}

export function EmptyState({ icon: Icon, headline, description, action }: Props) {
  return (
    <div className='flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border py-12 text-center'>
      <div className='rounded-full bg-muted p-3'>
        <Icon className='size-5 text-muted-foreground' />
      </div>
      <div className='space-y-1'>
        <p className='text-sm font-medium text-foreground'>{headline}</p>
        {description && (
          <p className='mx-auto max-w-xs text-xs text-muted-foreground'>{description}</p>
        )}
      </div>
      {action}
    </div>
  )
}
