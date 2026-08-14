import { Link } from '@tanstack/react-router'
import { Clock } from 'lucide-react'
import type { InProgressItem } from '@/lib/api/admin-dashboard'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

function initials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join('')
}

function formatElapsed(min: number): string {
  if (min < 1) return 'just now'
  if (min < 60) return `${min} min`
  const h = Math.floor(min / 60)
  const m = min % 60
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

export function InProgressList({ items }: { items: InProgressItem[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className='flex items-center gap-2 text-base'>
          <span className='relative flex size-2'>
            <span className='absolute inline-flex size-full animate-ping rounded-full bg-green-400 opacity-75' />
            <span className='relative inline-flex size-2 rounded-full bg-green-500' />
          </span>
          In progress now
          <span className='text-sm font-normal text-muted-foreground'>
            ({items.length})
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className='py-8 text-center text-sm text-muted-foreground'>
            No active attempts right now.
          </p>
        ) : (
          <ul className='space-y-1'>
            {items.map((item) => (
              <li key={item.attempt_id}>
                <Link
                  to='/results/$attemptId'
                  params={{ attemptId: item.attempt_id }}
                  className='flex items-center gap-3 rounded-md px-2 py-2 transition-colors hover:bg-muted/50'
                >
                  <span className='flex size-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary'>
                    {initials(item.student_name) || '?'}
                  </span>
                  <div className='min-w-0 flex-1'>
                    <p className='truncate text-sm font-medium'>
                      {item.student_name}
                    </p>
                    <p className='truncate text-xs text-muted-foreground'>
                      {item.test_name}
                    </p>
                  </div>
                  <div className='flex shrink-0 flex-col items-end gap-1'>
                    {item.current_section && (
                      <Badge variant='outline' className='text-[10px] capitalize'>
                        {item.current_section}
                      </Badge>
                    )}
                    <span className='flex items-center gap-1 text-xs text-muted-foreground'>
                      <Clock className='size-3' />
                      {formatElapsed(item.started_min_ago)}
                    </span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
