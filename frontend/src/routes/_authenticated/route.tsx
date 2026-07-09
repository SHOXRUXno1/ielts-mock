import { createFileRoute, redirect } from '@tanstack/react-router'
import { useAuthStore } from '@/stores/auth-store'
import { AuthenticatedLayout } from '@/components/layout/authenticated-layout'

export const Route = createFileRoute('/_authenticated')({
  beforeLoad: ({ location }) => {
    const { accessToken, user } = useAuthStore.getState().auth
    if (!accessToken) {
      throw redirect({
        to: '/login',
        search: { redirect: location.href },
      })
    }
    // Students who land on admin routes get redirected to their portal
    if (user && user.role === 'student') {
      throw redirect({ to: '/student/dashboard' })
    }
  },
  component: AuthenticatedLayout,
})
