import { useNavigate } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { EmptyState } from '@/components/report'
import { Button } from '@/components/ui/button'
import { fetchPracticeResults } from '@/lib/api/practice'
import { getDashboard, getMyResults } from '@/lib/api/student'
import { getDisplayNameInitials } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth-store'
import { LifetimePanel } from './components/lifetime-panel'
import { PreferencesPanel } from './components/preferences-panel'
import { ProfileHeader } from './components/profile-header'
import { ProfileSkeleton } from './components/profile-skeleton'
import { SignOutCard } from './components/sign-out-card'
import { SkillAveragesPanel } from './components/skill-averages-panel'
import { lifetimeStats, sessionExpiry } from './lib/profile-stats'

const EMPTY_BANDS = {
  listening: null,
  reading: null,
  writing: null,
  speaking: null,
}

export function StudentProfile() {
  const { auth } = useAuthStore()
  const navigate = useNavigate()
  const user = auth.user

  const dashboardQuery = useQuery({
    queryKey: ['student-dashboard'],
    queryFn: getDashboard,
  })
  const resultsQuery = useQuery({
    queryKey: ['student-results'],
    queryFn: () => getMyResults(),
  })
  const practiceQuery = useQuery({
    queryKey: ['student-practice-results'],
    queryFn: fetchPracticeResults,
  })

  const handleLogout = () => {
    auth.reset()
    void navigate({ to: '/login' })
  }

  if (
    dashboardQuery.isLoading ||
    resultsQuery.isLoading ||
    practiceQuery.isLoading
  ) {
    return <ProfileSkeleton />
  }

  if (dashboardQuery.isError) {
    return (
      <EmptyState
        title='Could not load your profile'
        description='Please try again in a moment.'
        action={
          <Button className='rounded-lg' onClick={() => void dashboardQuery.refetch()}>
            Retry
          </Button>
        }
      />
    )
  }

  const name = user?.full_name ?? user?.name ?? 'Student'
  const data = dashboardQuery.data
  const results = Array.isArray(resultsQuery.data) ? resultsQuery.data : []
  const practice = Array.isArray(practiceQuery.data) ? practiceQuery.data : []
  const lifetime = lifetimeStats(results, practice)

  return (
    <div className='space-y-6'>
      <div>
        <h1 className='text-2xl font-semibold tracking-tight text-foreground'>
          Profile
        </h1>
        <p className='mt-1 text-sm text-muted-foreground'>
          Your account, lifetime progress, and display preferences
        </p>
      </div>

      <ProfileHeader
        name={name}
        initials={getDisplayNameInitials(name)}
        login={user?.login}
        avgBand={data?.avg_band ?? null}
        sessionUntil={sessionExpiry(user?.exp)}
      />

      <div className='grid gap-6 lg:grid-cols-[minmax(0,1fr)_18rem]'>
        <div className='space-y-6'>
          <SkillAveragesPanel bands={data?.section_bands ?? EMPTY_BANDS} />
          <LifetimePanel
            mockTests={lifetime.mockTests}
            practiceSessions={lifetime.practiceSessions}
            bestBand={data?.best_band ?? null}
            activeSince={lifetime.activeSince}
          />
        </div>
        <div className='space-y-6'>
          <PreferencesPanel />
          <SignOutCard onConfirm={handleLogout} />
        </div>
      </div>
    </div>
  )
}
