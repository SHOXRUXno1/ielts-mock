import { Outlet, Link, useNavigate, useLocation } from '@tanstack/react-router'
import {
  BarChart3,
  BookOpen,
  Home,
  LogOut,
  Menu,
  User,
  X,
} from 'lucide-react'
import { useState } from 'react'
import { useAuthStore } from '@/stores/auth-store'
import { Button } from '@/components/ui/button'
import { ThemeSwitch } from '@/components/theme-switch'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { to: '/student/dashboard', label: 'Dashboard', icon: Home },
  { to: '/student/tests', label: 'Tests', icon: BookOpen },
  { to: '/student/results', label: 'Results', icon: BarChart3 },
  { to: '/student/profile', label: 'Profile', icon: User },
] as const

function isActive(pathname: string, to: string): boolean {
  if (to === '/student/dashboard') return pathname === '/student/dashboard'
  return pathname.startsWith(to)
}

export function StudentLayout() {
  const { auth } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const firstName = auth.user?.full_name ?? auth.user?.name ?? 'Student'
  const pathname = location.pathname
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const initials = firstName
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  const handleLogout = () => {
    auth.reset()
    void navigate({ to: '/login' })
  }

  return (
    <div className='flex min-h-svh flex-col bg-background'>
      {/* Desktop navigation */}
      <header className='sticky top-0 z-50 hidden border-b border-border bg-card/80 backdrop-blur-lg lg:block'>
        <div className='mx-auto flex h-16 max-w-6xl items-center justify-between px-6'>
          {/* Logo + nav */}
          <div className='flex items-center gap-10'>
            <Link
              to='/student/dashboard'
              className='flex items-center gap-2.5'
            >
              <span className='text-[15px] font-semibold text-foreground'>IELTS Mock</span>
            </Link>

            <nav className='flex items-center gap-1'>
              {NAV_ITEMS.map(({ to, label, icon: Icon }) => {
                const active = isActive(pathname, to)
                return (
                  <Link
                    key={to}
                    to={to}
                    className={cn(
                      'relative flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors',
                      active
                        ? 'text-foreground'
                        : 'text-muted-foreground hover:text-foreground hover:bg-muted/50',
                    )}
                  >
                    <Icon size={16} strokeWidth={active ? 2.2 : 1.8} />
                    {label}
                    {active && (
                      <span className='absolute inset-x-3 -bottom-[1.19rem] h-0.5 rounded-full bg-blue-600 dark:bg-blue-400' />
                    )}
                  </Link>
                )
              })}
            </nav>
          </div>

          {/* Right side */}
          <div className='flex items-center gap-3'>
            <ThemeSwitch />
            <div className='h-6 w-px bg-border' />
            <div className='flex items-center gap-2.5'>
              <div className='flex size-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-xs font-semibold text-white'>
                {initials}
              </div>
              <span className='text-sm font-medium text-foreground'>{firstName}</span>
            </div>
            <Button
              variant='ghost'
              size='sm'
              className='h-8 gap-1.5 rounded-lg text-muted-foreground hover:text-red-600 dark:hover:text-red-400'
              onClick={handleLogout}
            >
              <LogOut size={15} />
            </Button>
          </div>
        </div>
      </header>

      {/* Mobile top header */}
      <header className='sticky top-0 z-50 flex h-14 items-center justify-between border-b border-border bg-card/80 backdrop-blur-lg px-4 lg:hidden'>
        <Link
          to='/student/dashboard'
          className='flex items-center gap-2'
        >
          <span className='text-sm font-semibold text-foreground'>IELTS Mock</span>
        </Link>
        <div className='flex items-center gap-2'>
          <ThemeSwitch />
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className='flex size-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted'
          >
            {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </header>

      {/* Mobile dropdown menu */}
      {mobileMenuOpen && (
        <div className='fixed inset-x-0 top-14 z-40 border-b border-border bg-card p-4 shadow-lg lg:hidden'>
          <div className='flex items-center gap-3 mb-4 pb-4 border-b border-border'>
            <div className='flex size-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-sm font-semibold text-white'>
              {initials}
            </div>
            <div>
              <p className='text-sm font-medium text-foreground'>{firstName}</p>
              <p className='text-xs text-muted-foreground'>Student</p>
            </div>
          </div>
          <nav className='space-y-1'>
            {NAV_ITEMS.map(({ to, label, icon: Icon }) => {
              const active = isActive(pathname, to)
              return (
                <Link
                  key={to}
                  to={to}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                    active
                      ? 'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-400'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                  )}
                >
                  <Icon size={18} />
                  {label}
                </Link>
              )
            })}
          </nav>
          <div className='mt-4 pt-4 border-t border-border'>
            <button
              onClick={handleLogout}
              className='flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950'
            >
              <LogOut size={18} />
              Sign Out
            </button>
          </div>
        </div>
      )}

      {/* Page content */}
      <main className='mx-auto w-full max-w-5xl flex-1 px-4 py-6 pb-20 lg:px-6 lg:pb-6'>
        <Outlet />
      </main>

      {/* Mobile bottom tab bar */}
      <nav className='fixed inset-x-0 bottom-0 z-50 border-t border-border bg-card/80 backdrop-blur-lg lg:hidden'>
        <div className='mx-auto flex h-16 max-w-lg items-stretch'>
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => {
            const active = isActive(pathname, to)
            return (
              <Link
                key={to}
                to={to}
                className={cn(
                  'relative flex flex-1 flex-col items-center justify-center gap-0.5 text-[10px] font-medium transition-colors',
                  active
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-muted-foreground',
                )}
              >
                {active && (
                  <span className='absolute top-0 h-0.5 w-8 rounded-full bg-blue-600 dark:bg-blue-400' />
                )}
                <Icon size={20} strokeWidth={active ? 2.2 : 1.8} />
                {label}
              </Link>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
