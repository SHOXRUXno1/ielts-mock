import { createFileRoute, redirect } from '@tanstack/react-router'
import { useAuthStore } from '@/stores/auth-store'
import { TestLayout } from '@/components/layout/test-layout'

export const Route = createFileRoute('/_test')({
  beforeLoad: ({ location }) => {
    const { accessToken } = useAuthStore.getState().auth
    if (!accessToken) {
      throw redirect({
        to: '/login',
        search: { redirect: location.href },
      })
    }
  },
  component: TestLayout,
})
