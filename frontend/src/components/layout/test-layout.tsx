import { Outlet } from '@tanstack/react-router'
import { useAuthStore } from '@/stores/auth-store'
import { useStudentThemeScope } from '@/hooks/use-student-theme-scope'

export function TestLayout() {
  const isStudent = useAuthStore((state) => state.auth.user?.role === 'student')
  useStudentThemeScope(isStudent)

  return (
    <div
      className={
        isStudent
          ? 'flex h-svh flex-col bg-background text-foreground'
          : 'flex h-svh flex-col bg-white text-slate-900'
      }
    >
      <Outlet />
    </div>
  )
}
