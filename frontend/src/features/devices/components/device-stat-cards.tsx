import type { ComponentType, ReactNode } from 'react'
import { Activity, CalendarDays, Clock, Laptop } from 'lucide-react'
import type { DevicesSummary } from '@/lib/api/devices'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { relativeTime } from '../lib/format'

type DeviceStatCardsProps = {
  summary?: DevicesSummary
  isLoading?: boolean
}

function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  accent,
}: {
  label: string
  value: ReactNode
  hint?: string
  icon: ComponentType<{ className?: string }>
  accent?: 'online'
}) {
  return (
    <Card className='overflow-hidden'>
      <CardContent className='flex items-start gap-3 py-5'>
        <div
          className={cn(
            'flex size-10 shrink-0 items-center justify-center rounded-xl',
            accent === 'online'
              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
              : 'bg-muted text-muted-foreground'
          )}
        >
          <Icon className='size-5' />
        </div>
        <div className='min-w-0 flex-1'>
          <p className='text-xs font-medium tracking-wide text-muted-foreground uppercase'>
            {label}
          </p>
          <div className='mt-0.5 flex items-center gap-2'>
            {accent === 'online' && (
              <span className='relative flex size-2'>
                <span className='absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-75' />
                <span className='relative inline-flex size-2 rounded-full bg-emerald-500' />
              </span>
            )}
            <p className='truncate text-2xl font-semibold tabular-nums'>
              {value}
            </p>
          </div>
          {hint ? (
            <p className='mt-0.5 truncate text-xs text-muted-foreground'>
              {hint}
            </p>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}

export function DeviceStatCards({ summary, isLoading }: DeviceStatCardsProps) {
  if (isLoading || !summary) {
    return (
      <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className='flex items-start gap-3 py-5'>
              <Skeleton className='size-10 rounded-xl' />
              <div className='flex-1 space-y-2'>
                <Skeleton className='h-3 w-20' />
                <Skeleton className='h-7 w-12' />
                <Skeleton className='h-3 w-24' />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
      <StatCard
        label='Online now'
        value={summary.online_now}
        hint={
          summary.online_now === 1
            ? '1 active session'
            : `${summary.online_now} active sessions`
        }
        icon={Activity}
        accent='online'
      />
      <StatCard
        label='Logins today'
        value={summary.logins_today}
        hint='Since midnight'
        icon={CalendarDays}
      />
      <StatCard
        label='Devices 7d'
        value={summary.unique_devices_7d}
        hint='Unique browsers / IPs'
        icon={Laptop}
      />
      <StatCard
        label='Last login'
        value={
          summary.last_login_at
            ? relativeTime(summary.last_login_at)
            : '—'
        }
        hint='Most recent sign-in'
        icon={Clock}
      />
    </div>
  )
}
