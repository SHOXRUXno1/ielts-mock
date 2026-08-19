import { Link, Outlet, useLocation, useNavigate } from '@tanstack/react-router'
import { LogOut } from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ThemeSwitch } from '@/components/theme-switch'
import { isStudentNavActive, STUDENT_NAV } from '@/components/layout/data/student-nav'
import { useAuthStore } from '@/stores/auth-store'
import { cn } from '@/lib/utils'

function displayName(fullName?: string, name?: string): string {
  return fullName ?? name ?? 'Student'
}

function initialsFrom(name: string): string {
  return name
    .split(' ')
    .map((word) => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export function StudentLayout() {
  const { auth } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const name = displayName(auth.user?.full_name, auth.user?.name)
  const initials = initialsFrom(name)
  const pathname = location.pathname

  const handleLogout = () => {
    auth.reset()
    void navigate({ to: '/login' })
  }

  return (
    <div className='flex min-h-svh flex-col bg-background'>
      <header className='sticky top-0 z-50 border-b border-border bg-card/80 backdrop-blur-lg'>
        <div className='mx-auto flex h-14 max-w-5xl items-center justify-between px-4 lg:h-16 lg:px-6'>
          <div className='flex items-center gap-8'>
            <Link
              to='/student/dashboard'
              className='rounded-lg text-sm font-semibold text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none'
            >
              IELTS Mock
            </Link>
            <nav className='hidden items-center gap-1 lg:flex' aria-label='Student'>
              {STUDENT_NAV.map(({ to, label, icon: Icon }) => {
                const active = isStudentNavActive(pathname, to)
                return (
                  <Link
                    key={to}
                    to={to}
                    aria-current={active ? 'page' : undefined}
                    className={cn(
                      'relative flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                      'focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
                      'after:absolute after:inset-x-3 after:bottom-0 after:h-0.5 after:rounded-full after:bg-transparent',
                      active
                        ? 'text-foreground after:bg-foreground'
                        : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground',
                    )}
                  >
                    <Icon size={16} strokeWidth={active ? 2.2 : 1.8} />
                    {label}
                  </Link>
                )
              })}
            </nav>
          </div>

          <div className='flex items-center gap-2'>
            <ThemeSwitch />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  type='button'
                  className='flex items-center gap-2 rounded-lg p-1 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none'
                  aria-label='Account menu'
                >
                  <Avatar className='size-8'>
                    <AvatarFallback className='bg-muted text-xs font-semibold text-foreground'>
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                  <span className='hidden text-sm font-medium text-foreground sm:inline'>
                    {name}
                  </span>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align='end' className='w-48'>
                <DropdownMenuLabel className='font-normal'>
                  <p className='text-sm font-medium text-foreground'>{name}</p>
                  <p className='text-xs text-muted-foreground'>Student</p>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => void navigate({ to: '/student/profile' })}>
                  Profile
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  variant='destructive'
                  onClick={handleLogout}
                >
                  <LogOut />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <main className='mx-auto w-full max-w-5xl flex-1 px-4 py-6 pb-20 lg:px-6 lg:pb-6'>
        <Outlet />
      </main>

      <nav
        className='fixed inset-x-0 bottom-0 z-50 border-t border-border bg-card/80 backdrop-blur-lg lg:hidden'
        aria-label='Student'
      >
        <div className='mx-auto flex h-16 max-w-5xl items-stretch'>
          {STUDENT_NAV.map(({ to, label, icon: Icon }) => {
            const active = isStudentNavActive(pathname, to)
            return (
              <Link
                key={to}
                to={to}
                aria-current={active ? 'page' : undefined}
                className={cn(
                  'relative flex flex-1 flex-col items-center justify-center gap-1 text-xs font-medium transition-colors',
                  'focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
                  'after:absolute after:top-0 after:h-0.5 after:w-8 after:rounded-full after:bg-transparent',
                  active
                    ? 'text-foreground after:bg-foreground'
                    : 'text-muted-foreground',
                )}
              >
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
