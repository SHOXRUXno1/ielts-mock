import { Link } from '@tanstack/react-router'
import type { BandDistribution as BandDistributionData } from '@/lib/api/admin-dashboard'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { cn } from '@/lib/utils'

const BAR_COLORS: Record<string, string> = {
  '8-9': 'bg-green-500',
  '7-8': 'bg-blue-500',
  '6-7': 'bg-amber-500',
  '<6': 'bg-red-500',
}

export function BandDistribution({ data }: { data: BandDistributionData }) {
  const max = Math.max(...data.buckets.map((b) => b.count), 1)

  return (
    <Card>
      <CardHeader>
        <CardTitle className='flex flex-wrap items-baseline gap-2 text-base'>
          <span>Band distribution</span>
          <span className='text-sm font-normal text-muted-foreground'>
            last {data.period_days} days · {data.total_scored} scored attempt
            {data.total_scored !== 1 ? 's' : ''}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {data.total_scored === 0 ? (
          <p className='py-8 text-center text-sm text-muted-foreground'>
            No scored attempts in the last 30 days.
          </p>
        ) : (
          <div className='space-y-2.5'>
            {data.buckets.map((bucket) => (
              <Link
                key={bucket.range}
                to='/results'
                className='group flex items-center gap-3 rounded-md px-1 py-1 transition-colors hover:bg-muted/50'
              >
                <span className='w-10 shrink-0 text-sm font-medium text-muted-foreground'>
                  {bucket.range}
                </span>
                <div className='relative h-7 flex-1 overflow-hidden rounded bg-muted/40'>
                  <div
                    className={cn(
                      'absolute inset-y-0 left-0 rounded transition-all',
                      BAR_COLORS[bucket.range] ?? 'bg-primary',
                    )}
                    style={{ width: `${(bucket.count / max) * 100}%` }}
                  />
                </div>
                <span className='w-20 shrink-0 text-right text-sm tabular-nums text-muted-foreground'>
                  {bucket.percentage}%
                  <span className='ms-1 text-xs'>({bucket.count})</span>
                </span>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
