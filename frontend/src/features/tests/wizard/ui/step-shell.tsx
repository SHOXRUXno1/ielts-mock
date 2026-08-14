import type { ReactNode } from 'react'

type Props = {
  title: string
  description?: string
  counter?: ReactNode
  action?: ReactNode
  children: ReactNode
}

export function StepShell({ title, description, counter, action, children }: Props) {
  return (
    <div className='space-y-4'>
      <div className='flex items-center justify-between gap-3'>
        <div className='flex items-center gap-3'>
          <div>
            <h2 className='text-sm font-semibold text-foreground'>{title}</h2>
            {description && (
              <p className='mt-0.5 text-xs text-muted-foreground'>{description}</p>
            )}
          </div>
          {counter}
        </div>
        {action && <div className='shrink-0'>{action}</div>}
      </div>
      {children}
    </div>
  )
}
