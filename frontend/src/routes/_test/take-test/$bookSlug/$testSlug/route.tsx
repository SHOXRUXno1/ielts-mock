import { createFileRoute, redirect } from '@tanstack/react-router'
import { z } from 'zod'
import { TakeTestShell } from '@/features/tests/take/take-test-shell'
import { useAuthStore } from '@/stores/auth-store'

const searchSchema = z.object({
  resume: z.string().optional(),
})

export const Route = createFileRoute('/_test/take-test/$bookSlug/$testSlug')({
  validateSearch: searchSchema,
  beforeLoad: () => {
    if (useAuthStore.getState().auth.user?.role === 'student') {
      throw redirect({ to: '/student/tests' })
    }
  },
  component: LiveTakeShell,
})

function LiveTakeShell() {
  const { bookSlug, testSlug } = Route.useParams()
  const { resume } = Route.useSearch()
  return (
    <TakeTestShell
      mode='live'
      bookSlug={bookSlug}
      testSlug={testSlug}
      resume={resume}
    />
  )
}
