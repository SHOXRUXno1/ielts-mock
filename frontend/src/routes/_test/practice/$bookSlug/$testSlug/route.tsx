import { createFileRoute, Outlet, redirect } from '@tanstack/react-router'
import { z } from 'zod'
import { useAuthStore } from '@/stores/auth-store'

const searchSchema = z.object({
  attempt: z.string().uuid().optional(),
  scope: z.enum(['part', 'section']).catch('part'),
})

export const Route = createFileRoute('/_test/practice/$bookSlug/$testSlug')({
  validateSearch: searchSchema,
  beforeLoad: ({ params, search }) => {
    if (useAuthStore.getState().auth.user?.role === 'student') {
      throw redirect({ to: '/student/tests' })
    }
    // Practice URL must always include a section + part. Landing on the bare
    // /practice/:book/:test URL means the picker step was skipped — bounce
    // back to the catalog to pick a part.
    if (!search.attempt) {
      throw redirect({ to: '/student/tests' })
    }
    return { params, search }
  },
  component: () => <Outlet />,
})
