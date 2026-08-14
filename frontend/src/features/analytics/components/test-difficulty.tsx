import { Link } from '@tanstack/react-router'
import type { TestDifficulty } from '@/lib/api/analytics'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { cn } from '@/lib/utils'

function bandColor(band: number): string {
  if (band >= 8) return 'text-green-600 dark:text-green-400'
  if (band >= 7) return 'text-blue-600 dark:text-blue-400'
  if (band >= 6) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-600 dark:text-red-400'
}

export function TestDifficultyCard({
  tests,
}: {
  tests: TestDifficulty[]
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className='text-base'>Test difficulty</CardTitle>
        <CardDescription>Hardest tests by average band</CardDescription>
      </CardHeader>
      <CardContent>
        {tests.length === 0 ? (
          <p className='py-8 text-center text-sm text-muted-foreground'>
            No scored tests in this period.
          </p>
        ) : (
          <div className='space-y-1'>
            {tests.map((t, i) => (
              <Link
                key={t.test_id}
                to='/tests/$testId'
                params={{ testId: t.test_id }}
                className='flex items-center gap-3 rounded-md px-2 py-2 transition-colors hover:bg-muted/50'
              >
                <span className='flex size-5 shrink-0 items-center justify-center text-xs font-medium text-muted-foreground'>
                  {i + 1}
                </span>
                <div className='min-w-0 flex-1'>
                  <p className='truncate text-sm font-medium'>{t.title}</p>
                  <p className='text-xs text-muted-foreground'>
                    {t.attempts_count} attempt{t.attempts_count !== 1 ? 's' : ''}
                    {t.completion_rate != null && (
                      <> · {t.completion_rate}% completed</>
                    )}
                  </p>
                </div>
                <span
                  className={cn(
                    'text-lg font-semibold tabular-nums',
                    t.avg_band != null
                      ? bandColor(t.avg_band)
                      : 'text-muted-foreground',
                  )}
                >
                  {t.avg_band != null ? t.avg_band.toFixed(1) : '—'}
                </span>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
