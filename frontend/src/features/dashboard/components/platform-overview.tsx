import { Link } from '@tanstack/react-router'
import {
  ClipboardList,
  Gauge,
  Target,
  Users,
  type LucideIcon,
} from 'lucide-react'
import type { DashboardOverview } from '@/lib/api/admin-dashboard'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

function bandText(band: number): string {
  if (band >= 8) return 'text-green-600 dark:text-green-400'
  if (band >= 7) return 'text-blue-600 dark:text-blue-400'
  if (band >= 6) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-600 dark:text-red-400'
}

function Kpi({
  icon: Icon,
  iconClass,
  value,
  valueClass,
  label,
  sub,
  linkToResults,
}: {
  icon: LucideIcon
  iconClass: string
  value: string
  valueClass?: string
  label: string
  sub: string
  linkToResults?: boolean
}) {
  const body = (
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
        <p className={cn('text-2xl font-semibold tabular-nums leading-none', valueClass)}>
          {value}
        </p>
        <p className='mt-1 text-sm font-medium'>{label}</p>
        <p className='truncate text-xs text-muted-foreground'>{sub}</p>
      </div>
    </CardContent>
  )

  if (linkToResults) {
    return (
      <Card className='transition-colors hover:bg-muted/40'>
        <Link to='/results' className='block'>
          {body}
        </Link>
      </Card>
    )
  }
  return <Card>{body}</Card>
}

export function PlatformOverview({ data }: { data: DashboardOverview }) {
  return (
    <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
      <Kpi
        icon={Users}
        iconClass='bg-blue-500/10 text-blue-600 dark:text-blue-400'
        value={String(data.active_students_week)}
        label='Active students'
        sub={`this week · ${data.total_students} total`}
      />
      <Kpi
        icon={Target}
        iconClass='bg-green-500/10 text-green-600 dark:text-green-400'
        value={data.completion_rate != null ? `${data.completion_rate}%` : '—'}
        label='Completion rate'
        sub='finished vs abandoned · 30d'
      />
      <Kpi
        icon={Gauge}
        iconClass='bg-violet-500/10 text-violet-600 dark:text-violet-400'
        value={data.avg_band != null ? data.avg_band.toFixed(1) : '—'}
        valueClass={data.avg_band != null ? bandText(data.avg_band) : undefined}
        label='Average band'
        sub='all scored attempts · 30d'
      />
      <Kpi
        icon={ClipboardList}
        iconClass={cn(
          data.pending_evaluations > 0
            ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400'
            : 'bg-muted text-muted-foreground',
        )}
        value={String(data.pending_evaluations)}
        label='Pending reviews'
        sub={
          data.pending_evaluations > 0
            ? 'AI evaluations in queue'
            : 'all caught up'
        }
        linkToResults={data.pending_evaluations > 0}
      />
    </div>
  )
}
