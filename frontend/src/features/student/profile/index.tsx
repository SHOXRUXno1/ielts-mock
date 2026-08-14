import { useNavigate } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import {
  Award,
  BookOpen,
  ChevronRight,
  LogOut,
  Mail,
  Shield,
  TrendingUp,
  Trophy,
  User,
} from 'lucide-react'
import { getDashboard } from '@/lib/api/student'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/auth-store'
import { cn } from '@/lib/utils'

export function StudentProfile() {
  const { auth } = useAuthStore()
  const navigate = useNavigate()
  const user = auth.user

  const { data } = useQuery({
    queryKey: ['student-dashboard'],
    queryFn: getDashboard,
  })

  const initials = (user?.full_name ?? user?.name ?? 'S')
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  const handleLogout = () => {
    auth.reset()
    void navigate({ to: '/login' })
  }

  const statCards = [
    {
      label: 'Tests Taken',
      value: data?.tests_taken ?? 0,
      icon: BookOpen,
      gradient: 'from-blue-500 to-blue-600',
      bg: 'bg-blue-50 dark:bg-blue-950',
      iconColor: 'text-blue-600 dark:text-blue-400',
    },
    {
      label: 'Average Band',
      value: data?.avg_band != null ? data.avg_band.toFixed(1) : '—',
      icon: TrendingUp,
      gradient: 'from-amber-500 to-amber-600',
      bg: 'bg-amber-50 dark:bg-amber-950',
      iconColor: 'text-amber-600 dark:text-amber-400',
    },
    {
      label: 'Best Band',
      value: data?.best_band != null ? data.best_band.toFixed(1) : '—',
      icon: Trophy,
      gradient: 'from-emerald-500 to-emerald-600',
      bg: 'bg-emerald-50 dark:bg-emerald-950',
      iconColor: 'text-emerald-600 dark:text-emerald-400',
    },
  ]

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div>
        <h1 className='text-xl font-semibold tracking-tight text-foreground'>Profile</h1>
        <p className='mt-0.5 text-sm text-muted-foreground'>
          Your account details and performance overview
        </p>
      </div>

      {/* Profile card */}
      <div className='overflow-hidden rounded-2xl border border-border bg-card'>
        {/* Gradient header */}
        <div className='relative h-24 bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-600'>
          <div className='absolute inset-0 opacity-20' style={{ backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.15) 1px, transparent 1px)', backgroundSize: '20px 20px' }} />
        </div>

        <div className='relative px-6 pb-6'>
          {/* Avatar */}
          <div className='-mt-10 mb-4'>
            <div className='flex size-20 items-center justify-center rounded-2xl border-4 border-card bg-gradient-to-br from-blue-500 to-indigo-600 text-2xl font-bold text-white shadow-lg'>
              {initials}
            </div>
          </div>

          {/* Name & login */}
          <h2 className='text-lg font-semibold text-foreground'>
            {user?.full_name ?? user?.name ?? 'Student'}
          </h2>

          <div className='mt-3 flex flex-col gap-2'>
            {user?.login && (
              <div className='inline-flex items-center gap-2 text-sm text-muted-foreground'>
                <Mail size={14} className='shrink-0' />
                <span>{user.login}</span>
              </div>
            )}
            <div className='inline-flex items-center gap-2 text-sm text-muted-foreground'>
              <Shield size={14} className='shrink-0' />
              <span>Student account</span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div>
        <h3 className='mb-3 text-sm font-medium text-muted-foreground'>Performance</h3>
        <div className='grid grid-cols-1 gap-3 sm:grid-cols-3'>
          {statCards.map(({ label, value, icon: Icon, bg, iconColor }) => (
            <div
              key={label}
              className='flex items-center gap-3.5 rounded-2xl border border-border bg-card p-4 transition-shadow hover:shadow-md'
            >
              <div className={cn('flex size-11 items-center justify-center rounded-xl', bg)}>
                <Icon size={20} className={iconColor} />
              </div>
              <div>
                <p className='text-2xl font-bold text-foreground'>{value}</p>
                <p className='text-xs text-muted-foreground'>{label}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick links */}
      <div>
        <h3 className='mb-3 text-sm font-medium text-muted-foreground'>Quick Links</h3>
        <div className='overflow-hidden rounded-2xl border border-border bg-card divide-y divide-border'>
          <button
            onClick={() => void navigate({ to: '/student/results' })}
            className='flex w-full items-center gap-3 px-5 py-3.5 text-left transition-colors hover:bg-muted/50'
          >
            <div className='flex size-9 items-center justify-center rounded-lg bg-emerald-50 dark:bg-emerald-950'>
              <Award size={16} className='text-emerald-600 dark:text-emerald-400' />
            </div>
            <div className='flex-1'>
              <p className='text-sm font-medium text-foreground'>View Results</p>
              <p className='text-xs text-muted-foreground'>See all your test scores</p>
            </div>
            <ChevronRight size={16} className='text-muted-foreground' />
          </button>
          <button
            onClick={() => void navigate({ to: '/student/tests' })}
            className='flex w-full items-center gap-3 px-5 py-3.5 text-left transition-colors hover:bg-muted/50'
          >
            <div className='flex size-9 items-center justify-center rounded-lg bg-blue-50 dark:bg-blue-950'>
              <BookOpen size={16} className='text-blue-600 dark:text-blue-400' />
            </div>
            <div className='flex-1'>
              <p className='text-sm font-medium text-foreground'>Browse Tests</p>
              <p className='text-xs text-muted-foreground'>Start a new practice session</p>
            </div>
            <ChevronRight size={16} className='text-muted-foreground' />
          </button>
        </div>
      </div>

      {/* Sign out */}
      <div className='rounded-2xl border border-border bg-card p-5'>
        <Button
          variant='outline'
          className='w-full justify-center gap-2 rounded-lg border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 dark:border-red-900 dark:text-red-400 dark:hover:bg-red-950 dark:hover:text-red-300'
          onClick={handleLogout}
        >
          <LogOut size={16} />
          Sign Out
        </Button>
      </div>
    </div>
  )
}
