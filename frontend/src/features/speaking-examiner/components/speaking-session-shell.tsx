import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

type SpeakingSessionShellProps = {
  showPageHeader: boolean
  pageHeader: ReactNode
  banner?: ReactNode
  isActiveSession: boolean
  stage: ReactNode
  idleContent?: ReactNode
  doneContent?: ReactNode
  className?: string
}

export function SpeakingSessionShell({
  showPageHeader,
  pageHeader,
  banner,
  isActiveSession,
  stage,
  idleContent,
  doneContent,
  className,
}: SpeakingSessionShellProps) {
  if (isActiveSession) {
    return (
      <div className={cn('flex min-h-0 flex-1 flex-col', className)}>
        {banner}
        <div className='min-h-0 flex-1'>{stage}</div>
      </div>
    )
  }

  return (
    <div className={cn('flex min-h-0 flex-1 flex-col gap-4 md:gap-5', className)}>
      {showPageHeader && pageHeader}
      {banner}
      {stage}
      {idleContent}
      {doneContent}
    </div>
  )
}
