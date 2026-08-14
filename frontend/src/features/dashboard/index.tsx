import { useQuery } from '@tanstack/react-query'
import { getAdminDashboard } from '@/lib/api/admin-dashboard'
import { useAuthStore } from '@/stores/auth-store'
import { Skeleton } from '@/components/ui/skeleton'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { ActivityChart } from './components/activity-chart'
import { AttentionAlert } from './components/attention-alert'
import { BandDistribution } from './components/band-distribution'
import { InProgressList } from './components/in-progress-list'
import { PlatformOverview } from './components/platform-overview'
import { PopularTests } from './components/popular-tests'
import { RecentActivity } from './components/recent-activity'
import { SkillBreakdown } from './components/skill-breakdown'
import { StatCards } from './components/stat-cards'
import { TopStudents } from './components/top-students'

function greeting(): string {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 18) return 'Good afternoon'
  return 'Good evening'
}

export function Dashboard() {
  const user = useAuthStore((s) => s.auth.user)
  const name = user?.name || user?.full_name || user?.login || 'Admin'

  const { data, isLoading } = useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: getAdminDashboard,
    refetchInterval: 30000,
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
        <div className='mb-6'>
          <h1 className='text-2xl font-bold tracking-tight'>
            {greeting()}, {name}
          </h1>
          <p className='text-muted-foreground'>
            Here's what's happening on your platform today.
          </p>
        </div>

        {isLoading || !data ? (
          <div className='space-y-4'>
            <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
              {[0, 1, 2, 3].map((i) => (
                <Skeleton key={i} className='h-24' />
              ))}
            </div>
            <div className='grid gap-4 sm:grid-cols-3'>
              {[0, 1, 2].map((i) => (
                <Skeleton key={i} className='h-28' />
              ))}
            </div>
            <div className='grid gap-4 lg:grid-cols-3'>
              <Skeleton className='h-72 lg:col-span-2' />
              <Skeleton className='h-72' />
            </div>
            <div className='grid gap-4 lg:grid-cols-2'>
              <Skeleton className='h-56' />
              <Skeleton className='h-56' />
            </div>
            <div className='grid gap-4 lg:grid-cols-2'>
              <Skeleton className='h-64' />
              <Skeleton className='h-64' />
            </div>
            <Skeleton className='h-64' />
          </div>
        ) : (
          <div className='space-y-4'>
            <AttentionAlert alerts={data.alerts} />
            <PlatformOverview data={data.overview} />
            <StatCards stats={data.stats} />
            <div className='grid gap-4 lg:grid-cols-3'>
              <div className='lg:col-span-2'>
                <ActivityChart data={data.activity_chart} />
              </div>
              <div className='lg:col-span-1'>
                <InProgressList items={data.in_progress} />
              </div>
            </div>
            <div className='grid gap-4 lg:grid-cols-2'>
              <BandDistribution data={data.band_distribution} />
              <SkillBreakdown skills={data.skill_breakdown} />
            </div>
            <div className='grid gap-4 lg:grid-cols-2'>
              <TopStudents students={data.top_students} />
              <PopularTests tests={data.popular_tests} />
            </div>
            <RecentActivity items={data.recent_activity} />
          </div>
        )}
      </Main>
    </>
  )
}
