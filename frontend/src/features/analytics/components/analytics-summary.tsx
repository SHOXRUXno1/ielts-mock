import {
  Activity,
  CheckCircle2,
  Gauge,
  Users,
  type LucideIcon,
} from 'lucide-react'
import type { AnalyticsSummary } from '@/lib/api/analytics'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

function bandColor(band: number): string {
  if (band >= 8) return 'text-green-600 dark:text-green-400'
  if (band >= 7) return 'text-blue-600 dark:text-blue-400'
  if (band >= 6) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-600 dark:text-red-400'
}

function Tile({
  icon: Icon,
  iconClass,
  value,
  valueClass,
  label,
  sub,
}: {
  icon: LucideIcon
  iconClass: string
  value: string
  valueClass?: string
  label: string
  sub: string
}) {
  return (
    <Card>
      <CardContent className='flex items-center gap-4 py-5'>
        <span
          className={cn(
            'flex size-11 shrink-0 items-center justify-center rounded-full',
            iconClass,
          )}
        >
          <Icon className='size-5' />
        </span>
        <div className='min-w-0'>
          <p
            className={cn(
              'text-2xl font-semibold tabular-nums leading-none',
              valueClass,
            )}
          >
            {value}
          </p>
          <p className='mt-1 text-sm font-medium'>{label}</p>
          <p className='truncate text-xs text-muted-foreground'>{sub}</p>
        </div>
      </CardContent>
    </Card>
  )
}

export function AnalyticsSummaryCards({
  summary,
  days,
}: {
  summary: AnalyticsSummary
  days: number
}) {
  return (
    <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
      <Tile
        icon={Activity}
        iconClass='bg-blue-500/10 text-blue-600 dark:text-blue-400'
        value={String(summary.total_attempts)}
        label='Total attempts'
        sub={`last ${days} days`}
      />
      <Tile
        icon={CheckCircle2}
        iconClass='bg-green-500/10 text-green-600 dark:text-green-400'
        value={
          summary.completion_rate != null ? `${summary.completion_rate}%` : '—'
        }
        label='Completion rate'
        sub={`${summary.completed_attempts} completed`}
      />
      <Tile
        icon={Gauge}
        iconClass='bg-violet-500/10 text-violet-600 dark:text-violet-400'
        value={summary.avg_band != null ? summary.avg_band.toFixed(1) : '—'}
        valueClass={
          summary.avg_band != null ? bandColor(summary.avg_band) : undefined
        }
        label='Average band'
        sub={`scored attempts · ${days}d`}
      />
      <Tile
        icon={Users}
        iconClass='bg-amber-500/10 text-amber-600 dark:text-amber-400'
        value={String(summary.active_students)}
        label='Active students'
        sub={`with attempts · ${days}d`}
      />
    </div>
  )
}
