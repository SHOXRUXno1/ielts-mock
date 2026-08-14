import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useAuthStore } from '@/stores/auth-store'
import { Dashboard } from '@/features/dashboard'
import { useEffect } from 'react'

function HomeRedirect() {
  const { user } = useAuthStore.getState().auth
  const navigate = useNavigate()

  useEffect(() => {
    if (user?.role === 'student') {
      void navigate({ to: '/student/dashboard' })
    }
  }, [user, navigate])

  if (!user || user.role === 'admin') {
    return <Dashboard />
  }

  return null
}

export const Route = createFileRoute('/_authenticated/')({
  component: HomeRedirect,
})
