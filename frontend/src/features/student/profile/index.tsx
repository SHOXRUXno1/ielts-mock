import { useNavigate } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { EmptyState } from '@/components/report'
import { Button } from '@/components/ui/button'
import { getDashboard } from '@/lib/api/student'
import { useAuthStore } from '@/stores/auth-store'
import { IdentityPanel } from './components/identity-panel'
import { PerformancePanel } from './components/performance-panel'
import { ProfileSkeleton } from './components/profile-skeleton'
import { QuickLinks } from './components/quick-links'
import { SignOutCard } from './components/sign-out-card'

export function StudentProfile() {
  const { auth } = useAuthStore()
  const navigate = useNavigate()
  const user = auth.user
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['student-dashboard'],
    queryFn: getDashboard,
  })

  const name = user?.full_name ?? user?.name ?? 'Student'
  const initials = name
    .split(' ')
    .map((word) => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  const handleLogout = () => {
    auth.reset()
    void navigate({ to: '/login' })
  }

  if (isLoading) return <ProfileSkeleton />

  if (isError) {
    return (
      <EmptyState
        title='Could not load your profile'
        description='Please try again in a moment.'
        action={
          <Button className='rounded-lg' onClick={() => void refetch()}>
            Retry
          </Button>
        }
      />
    )
  }

  return (
    <div className='space-y-6'>
      <div>
        <h1 className='text-2xl font-semibold tracking-tight text-foreground'>
          Profile
        </h1>
        <p className='mt-1 text-sm text-muted-foreground'>
          Your account details and performance overview
        </p>
      </div>

      <IdentityPanel name={name} initials={initials} login={user?.login} />
      <PerformancePanel
        testsTaken={data?.tests_taken ?? 0}
        avgBand={data?.avg_band ?? null}
        bestBand={data?.best_band ?? null}
      />
      <QuickLinks />
      <SignOutCard onConfirm={handleLogout} />
    </div>
  )
}
