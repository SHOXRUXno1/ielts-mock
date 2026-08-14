import { Link } from '@tanstack/react-router'
import { CheckCircle, FileText, PlayCircle } from 'lucide-react'
import type { RecentActivityItem } from '@/lib/api/admin-dashboard'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { cn } from '@/lib/utils'

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

const EVENT_CONFIG = {
  started: {
    icon: PlayCircle,
    iconClass: 'text-blue-500',
    verb: 'started',
  },
  finished: {
    icon: CheckCircle,
    iconClass: 'text-green-500',
    verb: 'finished',
  },
  submitted_writing: {
    icon: FileText,
    iconClass: 'text-amber-500',
    verb: 'submitted Writing for',
  },
} as const

export function RecentActivity({ items }: { items: RecentActivityItem[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className='text-base'>Recent activity</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className='py-8 text-center text-sm text-muted-foreground'>
            No recent activity.
          </p>
        ) : (
          <div className='max-h-80 space-y-0.5 overflow-y-auto'>
            {items.map((item, i) => {
              const cfg = EVENT_CONFIG[item.type] ?? EVENT_CONFIG.started
              const Icon = cfg.icon
              return (
                <Link
                  key={`${item.attempt_id}-${item.type}-${i}`}
                  to='/results/$attemptId'
                  params={{ attemptId: item.attempt_id }}
                  className='flex items-center gap-3 rounded-md px-2 py-2 transition-colors hover:bg-muted/50'
                >
                  <Icon className={cn('size-4 shrink-0', cfg.iconClass)} />
                  <span className='w-14 shrink-0 text-xs tabular-nums text-muted-foreground'>
                    {formatRelativeTime(item.timestamp)}
                  </span>
                  <p className='min-w-0 flex-1 truncate text-sm'>
                    <span className='font-medium'>{item.student_name}</span>
                    <span className='text-muted-foreground'>
                      {' '}{cfg.verb}{' '}
                    </span>
                    <span className='font-medium'>{item.test_name}</span>
                  </p>
                  {item.type === 'finished' && item.band != null && (
                    <Badge variant='outline' className='shrink-0 tabular-nums'>
                      {item.band.toFixed(1)}
                    </Badge>
                  )}
                </Link>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
