import { Outlet, Link, useNavigate } from '@tanstack/react-router'
import { LogOut, BookOpen } from 'lucide-react'
import { useAuthStore } from '@/stores/auth-store'
import { Button } from '@/components/ui/button'

export function StudentLayout() {
  const { auth } = useAuthStore()
  const navigate = useNavigate()
  const firstName = auth.user?.full_name ?? auth.user?.name ?? 'Student'

  const handleLogout = () => {
    auth.reset()
    void navigate({ to: '/login' })
  }

  return (
    <div className='min-h-svh flex flex-col bg-muted/20'>
      {/* Header */}
      <header className='sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60'>
        <div className='mx-auto flex h-14 max-w-5xl items-center justify-between px-4'>
          <Link to='/student/dashboard' className='flex items-center gap-2 font-semibold'>
            <BookOpen size={18} className='text-primary' />
            <span>IELTS Mock</span>
          </Link>

          <div className='flex items-center gap-3'>
            <span className='text-sm text-muted-foreground hidden sm:inline'>
              Welcome, <span className='font-medium text-foreground'>{firstName}</span>
            </span>
            <Button variant='ghost' size='sm' onClick={handleLogout}>
              <LogOut size={14} className='mr-1.5' />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className='mx-auto w-full max-w-5xl flex-1 px-4 py-6'>
        <Outlet />
      </main>
    </div>
  )
}
