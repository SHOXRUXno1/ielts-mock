import { createFileRoute } from '@tanstack/react-router'
import { StudentLogin } from '@/features/auth/student-login'
import { parseSafeRedirect } from '@/lib/safe-redirect'

export const Route = createFileRoute('/(auth)/login')({
  validateSearch: (search: Record<string, unknown>): { redirect?: string } => {
    const redirect = parseSafeRedirect(search.redirect)
    return redirect ? { redirect } : {}
  },
  component: StudentLogin,
})
