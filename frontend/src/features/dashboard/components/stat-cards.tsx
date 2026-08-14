import { Minus, TrendingDown, TrendingUp } from 'lucide-react'
import type { DashboardStats, StatPoint } from '@/lib/api/admin-dashboard'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

function DeltaBadge({ value, suffix }: { value: number | null | undefined; suffix: string }) {
  if (value == null) {
    return <span className='text-xs text-muted-foreground'>no prior data</span>
  }
  const positive = value > 0
  const negative = value < 0
  const Icon = positive ? TrendingUp : negative ? TrendingDown : Minus
  const sign = positive ? '+' : ''
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 text-xs font-medium',
        positive && 'text-green-600 dark:text-green-400',
        negative && 'text-red-600 dark:text-red-400',
        !positive && !negative && 'text-muted-foreground',
      )}
    >
      <Icon className='size-3.5' />
      {sign}
      {value}
      {suffix}
    </span>
  )
}

function StatCard({
  label,
  stat,
  mode,
}: {
  label: string
  stat: StatPoint
  mode: 'absolute' | 'percent'
}) {
  return (
    <Card>
      <CardContent className='flex flex-col gap-1.5 py-5'>
        <p className='text-xs font-medium tracking-wide text-muted-foreground uppercase'>
          {label}
        </p>
        <p className='text-2xl font-semibold tabular-nums'>
          {stat.attempts}
          <span className='ms-1.5 text-sm font-normal text-muted-foreground'>
            attempt{stat.attempts !== 1 ? 's' : ''}
          </span>
        </p>
        {mode === 'absolute' ? (
          <DeltaBadge value={stat.delta_vs_yesterday} suffix=' vs yesterday' />
        ) : (
          <DeltaBadge value={stat.delta_percent} suffix='% vs prev' />
        )}
      </CardContent>
    </Card>
  )
}

export function StatCards({ stats }: { stats: DashboardStats }) {
  return (
    <div className='grid gap-4 sm:grid-cols-3'>
      <StatCard label='Today' stat={stats.today} mode='absolute' />
      <StatCard label='This week' stat={stats.week} mode='percent' />
      <StatCard label='This month' stat={stats.month} mode='percent' />
    </div>
  )
}
