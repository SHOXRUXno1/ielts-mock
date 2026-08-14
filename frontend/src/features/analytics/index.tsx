import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearch as useRouteSearch } from '@tanstack/react-router'
import { getAnalytics } from '@/lib/api/analytics'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { AnalyticsSummaryCards } from './components/analytics-summary'
import { BandTrendChart } from './components/band-trend-chart'
import { CompletionBreakdownCard } from './components/completion-breakdown'
import { GroupComparisonCard } from './components/group-comparison'
import { SectionAveragesCard } from './components/section-averages'
import { TestDifficultyCard } from './components/test-difficulty'

const PERIOD_OPTIONS = [7, 30, 90] as const

export function Analytics() {
  const { days: searchDays } = useRouteSearch({ strict: false }) as {
    days?: number
  }
  const [days, setDays] = useState<number>(
    searchDays && PERIOD_OPTIONS.includes(searchDays as 7 | 30 | 90)
      ? searchDays
      : 30,
  )

  const { data, isLoading } = useQuery({
    queryKey: ['analytics', days],
    queryFn: () => getAnalytics(days),
  })

  return (
    <>
      <Header>
        <Search className='me-auto' />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main>
        <div className='mb-6 flex flex-wrap items-end justify-between gap-4'>
          <div>
            <h1 className='text-2xl font-bold tracking-tight'>Analytics</h1>
            <p className='text-muted-foreground'>
              Performance trends and insights across your platform.
            </p>
          </div>

          <div className='flex items-center rounded-lg border p-0.5 gap-0.5'>
            {PERIOD_OPTIONS.map((d) => (
              <Button
                key={d}
                size='sm'
                variant={days === d ? 'default' : 'ghost'}
                className='h-7 px-3 text-xs'
                onClick={() => setDays(d)}
              >
                {d}d
              </Button>
            ))}
          </div>
        </div>

        {isLoading || !data ? (
          <div className='space-y-4'>
            <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
              {[0, 1, 2, 3].map((i) => (
                <Skeleton key={i} className='h-24' />
              ))}
            </div>
            <Skeleton className='h-80' />
            <div className='grid gap-4 lg:grid-cols-2'>
              <Skeleton className='h-64' />
              <Skeleton className='h-64' />
            </div>
            <div className='grid gap-4 lg:grid-cols-2'>
              <Skeleton className='h-72' />
              <Skeleton className='h-72' />
            </div>
          </div>
        ) : (
          <div className='space-y-4'>
            <AnalyticsSummaryCards summary={data.summary} days={days} />
            <BandTrendChart data={data.band_trend} days={days} />
            <div className='grid gap-4 lg:grid-cols-2'>
              <SectionAveragesCard sections={data.section_averages} days={days} />
              <CompletionBreakdownCard data={data.completion} />
            </div>
            <div className='grid gap-4 lg:grid-cols-2'>
              <TestDifficultyCard tests={data.test_difficulty} />
              <GroupComparisonCard groups={data.group_comparison} />
            </div>
          </div>
        )}
      </Main>
    </>
  )
}
