import type { GroupComparison } from '@/lib/api/analytics'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { cn } from '@/lib/utils'

function bandFill(band: number): string {
  if (band >= 8) return 'bg-green-500'
  if (band >= 7) return 'bg-blue-500'
  if (band >= 6) return 'bg-amber-500'
  return 'bg-red-500'
}

function bandText(band: number): string {
  if (band >= 8) return 'text-green-600 dark:text-green-400'
  if (band >= 7) return 'text-blue-600 dark:text-blue-400'
  if (band >= 6) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-600 dark:text-red-400'
}

export function GroupComparisonCard({
  groups,
}: {
  groups: GroupComparison[]
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className='text-base'>Group comparison</CardTitle>
        <CardDescription>Performance by student group</CardDescription>
      </CardHeader>
      <CardContent>
        {groups.length === 0 ? (
          <p className='py-8 text-center text-sm text-muted-foreground'>
            No group data available.
          </p>
        ) : (
          <div className='space-y-3'>
            {groups.map((g) => {
              const band = g.avg_band
              return (
                <div
                  key={g.group_name}
                  className='flex items-center gap-3 rounded-md px-2 py-1.5'
                >
                  <div className='min-w-0 flex-1'>
                    <p className='truncate text-sm font-medium'>
                      {g.group_name}
                    </p>
                    <p className='text-xs text-muted-foreground'>
                      {g.students} student{g.students !== 1 ? 's' : ''} ·{' '}
                      {g.attempts_count} attempt
                      {g.attempts_count !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <div className='relative h-2 w-24 shrink-0 overflow-hidden rounded-full bg-muted/40'>
                    {band != null && (
                      <div
                        className={cn(
                          'absolute inset-y-0 left-0 rounded-full',
                          bandFill(band),
                        )}
                        style={{ width: `${(band / 9) * 100}%` }}
                      />
                    )}
                  </div>
                  <span
                    className={cn(
                      'w-10 shrink-0 text-right text-sm font-semibold tabular-nums',
                      band != null ? bandText(band) : 'text-muted-foreground',
                    )}
                  >
                    {band != null ? band.toFixed(1) : '—'}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
