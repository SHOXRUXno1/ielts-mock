import { createFileRoute, redirect } from '@tanstack/react-router'
import { useAuthStore } from '@/stores/auth-store'
import { StudentLayout } from '@/components/layout/student-layout'

export const Route = createFileRoute('/_student')({
  beforeLoad: () => {
    const { accessToken, user } = useAuthStore.getState().auth
    if (!accessToken) {
      throw redirect({ to: '/login' })
    }
    // If user data is loaded and it's an admin, send to admin panel
    if (user && user.role === 'admin') {
      throw redirect({ to: '/' })
    }
  },
  component: StudentLayout,
})
