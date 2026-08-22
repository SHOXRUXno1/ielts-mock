import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle,
  CheckCircle2,
  CircleHelp,
  RefreshCw,
  XCircle,
} from 'lucide-react'
import { fetchUsage, type ProviderStatus, type ProviderUsage } from '@/lib/api/usage'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { ThemeSwitch } from '@/components/theme-switch'

const REFETCH_MS = 60_000

const STATUS_META: Record<
  ProviderStatus,
  { icon: typeof CheckCircle2; label: string; className: string; bar: string }
> = {
  ok: {
    icon: CheckCircle2,
    label: 'Healthy',
    className:
      'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400',
    bar: 'bg-emerald-500',
  },
  warning: {
    icon: AlertTriangle,
    label: 'Running low',
    className:
      'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400',
    bar: 'bg-amber-500',
  },
  error: {
    icon: XCircle,
    label: 'Attention',
    className: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400',
    bar: 'bg-red-500',
  },
  unknown: {
    icon: CircleHelp,
    label: 'No data',
    className: 'bg-muted text-muted-foreground',
    bar: 'bg-muted-foreground',
  },
}

function formatNumber(value: number | null | undefined): string {
  if (value == null) return '—'
  return value.toLocaleString('en-US')
}

function formatMoney(value: string | null | undefined): string {
  if (value == null || value === '') return '—'
  const n = Number(value)
  if (Number.isNaN(n)) return value
  return `$${n.toFixed(2)}`
}

function formatWhen(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString(undefined, {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className='flex items-baseline justify-between gap-3 text-sm'>
      <span className='text-muted-foreground'>{label}</span>
      <span className='truncate font-medium tabular-nums'>{value}</span>
    </div>
  )
}

/** The detail rows differ per provider, because each exposes different data. */
function ProviderDetails({ p }: { p: ProviderUsage }) {
  if (!p.configured) {
    return (
      <p className='text-sm text-muted-foreground'>
        {p.detail ?? 'Not configured'}
      </p>
    )
  }

  switch (p.name) {
    case 'DigitalOcean':
      return (
        <div className='space-y-3'>
          <div>
            <p className='text-xs text-muted-foreground'>Total due now</p>
            <p className='text-2xl font-bold tabular-nums'>
              {formatMoney(p.month_to_date_balance)}
            </p>
          </div>
          <div className='space-y-2'>
            <Row
              label='Spent this month'
              value={formatMoney(p.month_to_date_usage)}
            />
            <Row
              label='Carried over'
              value={formatMoney(p.account_balance)}
            />
            <Row label='As of' value={formatWhen(p.generated_at)} />
          </div>
        </div>
      )

    case 'Gemini':
      return (
        <div className='space-y-2'>
          <Row label='Model' value={p.model ?? '—'} />
          <Row
            label='API keys'
            value={`${p.key_count ?? 0} × ${p.rpm_per_key ?? 0} req/min`}
          />
          <Row label='Throttled today' value={formatNumber(p.rate_limited_today)} />
          <Row label='Counting since' value={formatWhen(p.counting_since)} />
        </div>
      )

    case 'Groq':
      return (
        <div className='space-y-2'>
          <Row label='Speech-to-text' value={p.stt_model ?? '—'} />
          <Row label='Examiner model' value={p.model ?? '—'} />
          <Row
            label='Requests left in window'
            value={
              p.remaining_requests != null
                ? `${p.remaining_requests} / ${p.limit_requests ?? '?'}`
                : '—'
            }
          />
          <Row
            label='Audio seconds left'
            value={
              p.remaining_audio_seconds != null
                ? `${p.remaining_audio_seconds} / ${p.limit_audio_seconds ?? '?'}`
                : '—'
            }
          />
          <Row label='Last seen' value={formatWhen(p.observed_at)} />
          {p.detail && (
            <p className='pt-1 text-xs text-muted-foreground'>{p.detail}</p>
          )}
        </div>
      )

    case 'ElevenLabs':
      return (
        <div className='space-y-2'>
          <Row label='Plan' value={p.tier ?? '—'} />
          <Row label='Characters used' value={formatNumber(p.used)} />
          <Row label='Plan limit' value={formatNumber(p.limit)} />
          <Row label='Quota resets' value={formatWhen(p.resets_at)} />
        </div>
      )

    case 'Simli':
      return (
        <div className='space-y-2'>
          <Row
            label='Concurrent sessions'
            value={`up to ${p.max_concurrent ?? '?'}`}
          />
          {p.detail && (
            <p className='pt-1 text-xs text-muted-foreground'>{p.detail}</p>
          )}
        </div>
      )

    default:
      return p.detail ? (
        <p className='text-sm text-muted-foreground'>{p.detail}</p>
      ) : null
  }
}

function ProviderCard({ p }: { p: ProviderUsage }) {
  const meta = STATUS_META[p.status] ?? STATUS_META.unknown
  const Icon = meta.icon
  const showBar = p.percent_left != null

  return (
    <div className='flex flex-col gap-4 rounded-xl border bg-card p-5'>
      <div className='flex items-start justify-between gap-3'>
        <div className='min-w-0'>
          <h3 className='truncate font-semibold'>{p.name}</h3>
          {p.estimated && (
            <p className='mt-0.5 text-xs text-muted-foreground'>
              Estimated from our own call count
            </p>
          )}
        </div>
        <Badge className={cn('shrink-0 gap-1 border-0', meta.className)}>
          <Icon className='size-3' />
          {p.configured ? meta.label : 'Not set up'}
        </Badge>
      </div>

      {showBar && (
        <div className='space-y-1.5'>
          <div className='flex items-baseline justify-between'>
            <span className='text-2xl font-bold tabular-nums'>
              {p.percent_left}%
            </span>
            <span className='text-xs text-muted-foreground'>
              {formatNumber(p.remaining)} {p.unit} left
            </span>
          </div>
          <div
            className='h-1.5 w-full overflow-hidden rounded-full bg-muted'
            role='progressbar'
            aria-valuenow={p.percent_left ?? 0}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${p.name} quota remaining`}
          >
            <div
              className={cn('h-full rounded-full transition-all', meta.bar)}
              style={{ width: `${Math.min(100, Math.max(0, p.percent_left ?? 0))}%` }}
            />
          </div>
        </div>
      )}

      <ProviderDetails p={p} />
    </div>
  )
}

export function Usage() {
  const { data, isLoading, isFetching, refetch, isError } = useQuery({
    queryKey: ['admin-usage'],
    queryFn: fetchUsage,
    refetchInterval: REFETCH_MS,
  })

  return (
    <>
      <Header fixed>
        <div className='me-auto' />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main className='flex flex-1 flex-col gap-6'>
        <div className='flex flex-wrap items-end justify-between gap-4'>
          <div>
            <h1 className='text-2xl font-bold tracking-tight'>Usage & Billing</h1>
            <p className='mt-1 text-sm text-muted-foreground'>
              How much quota is left on each paid service this platform depends on.
            </p>
          </div>
          <div className='flex items-center gap-3'>
            {data && (
              <span className='text-xs text-muted-foreground'>
                Updated {formatWhen(data.generated_at)}
              </span>
            )}
            <Button
              variant='outline'
              size='sm'
              className='gap-1.5'
              disabled={isFetching}
              onClick={() => void refetch()}
            >
              <RefreshCw
                className={cn('size-3.5', isFetching && 'animate-spin')}
              />
              Refresh
            </Button>
          </div>
        </div>

        {isError ? (
          <div className='rounded-xl border bg-card py-16 text-center'>
            <XCircle className='mx-auto size-8 text-red-500' />
            <p className='mt-3 font-medium'>Could not load usage data</p>
            <p className='mt-1 text-sm text-muted-foreground'>
              The server rejected the request. Check that you are signed in as an
              admin.
            </p>
          </div>
        ) : isLoading || !data ? (
          <div className='grid gap-4 md:grid-cols-2 xl:grid-cols-3'>
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className='h-52 rounded-xl' />
            ))}
          </div>
        ) : (
          <div className='grid gap-4 md:grid-cols-2 xl:grid-cols-3'>
            {data.providers.map((p) => (
              <ProviderCard key={p.name} p={p} />
            ))}
          </div>
        )}

        <p className='text-xs text-muted-foreground'>
          Gemini has no quota API, so its figure is our own tally of calls since
          the last redeploy compared against the free-tier daily allowance. Groq
          reports its ceiling only on a real request, so the numbers here are from
          the most recent one. Simli exposes no quota at all — an exhausted plan
          shows up as a failed Speaking session.
        </p>
      </Main>
    </>
  )
}
