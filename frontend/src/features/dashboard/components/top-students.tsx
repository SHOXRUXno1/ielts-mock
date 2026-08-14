import { Link } from '@tanstack/react-router'
import type { TopStudent } from '@/lib/api/admin-dashboard'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { cn } from '@/lib/utils'

function initials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join('')
}

function bandColor(band: number): string {
  if (band >= 8) return 'text-green-600 dark:text-green-400'
  if (band >= 7) return 'text-blue-600 dark:text-blue-400'
  if (band >= 6) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-600 dark:text-red-400'
}

export function TopStudents({ students }: { students: TopStudent[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className='text-base'>Top performing students</CardTitle>
        <CardDescription>Last 30 days · min 3 attempts</CardDescription>
      </CardHeader>
      <CardContent>
        {students.length === 0 ? (
          <p className='py-8 text-center text-sm text-muted-foreground'>
            Not enough data yet — students need at least 3 completed attempts.
          </p>
        ) : (
          <ul className='space-y-1'>
            {students.map((s, i) => (
              <li key={s.student_id}>
                <Link
                  to='/results/students/$studentId'
                  params={{ studentId: s.student_id }}
                  className='flex items-center gap-3 rounded-md px-2 py-2 transition-colors hover:bg-muted/50'
                >
                  <span className='flex size-5 shrink-0 items-center justify-center text-xs font-medium text-muted-foreground'>
                    {i + 1}
                  </span>
                  <span className='flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary'>
                    {initials(s.name) || '?'}
                  </span>
                  <div className='min-w-0 flex-1'>
                    <p className='truncate text-sm font-medium'>{s.name}</p>
                    <p className='text-xs text-muted-foreground'>
                      {s.attempts_count} attempt{s.attempts_count !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <span className={cn('text-lg font-semibold tabular-nums', bandColor(s.avg_band))}>
                    {s.avg_band.toFixed(1)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
