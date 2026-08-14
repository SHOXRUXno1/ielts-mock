import { Link } from '@tanstack/react-router'
import type { PopularTest } from '@/lib/api/admin-dashboard'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export function PopularTests({ tests }: { tests: PopularTest[] }) {
  const max = Math.max(...tests.map((t) => t.attempts_count), 1)

  return (
    <Card>
      <CardHeader>
        <CardTitle className='text-base'>Popular tests</CardTitle>
        <CardDescription>Last 30 days</CardDescription>
      </CardHeader>
      <CardContent>
        {tests.length === 0 ? (
          <p className='py-8 text-center text-sm text-muted-foreground'>
            No test attempts in the last 30 days.
          </p>
        ) : (
          <ul className='space-y-3'>
            {tests.map((t) => (
              <li key={t.test_id}>
                <Link
                  to='/tests/$testId'
                  params={{ testId: t.test_id }}
                  className='block rounded-md px-2 py-2 transition-colors hover:bg-muted/50'
                >
                  <div className='mb-1.5 flex items-baseline justify-between gap-2'>
                    <p className='truncate text-sm font-medium'>{t.title}</p>
                    <span className='shrink-0 text-xs tabular-nums text-muted-foreground'>
                      {t.attempts_count} attempt{t.attempts_count !== 1 ? 's' : ''}
                      {t.avg_band != null && (
                        <> · avg {t.avg_band.toFixed(1)}</>
                      )}
                    </span>
                  </div>
                  <div className='relative h-1.5 overflow-hidden rounded-full bg-muted/40'>
                    <div
                      className='absolute inset-y-0 left-0 rounded-full bg-primary/60'
                      style={{ width: `${(t.attempts_count / max) * 100}%` }}
                    />
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
