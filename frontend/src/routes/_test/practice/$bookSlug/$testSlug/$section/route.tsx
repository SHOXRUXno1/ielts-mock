import { createFileRoute, Outlet, redirect } from '@tanstack/react-router'
import { isSectionType } from '@/features/tests/lib/part-resolver'

export const Route = createFileRoute(
  '/_test/practice/$bookSlug/$testSlug/$section',
)({
  beforeLoad: ({ params }) => {
    if (!isSectionType(params.section)) {
      throw redirect({ to: '/student/tests' })
    }
  },
  component: () => <Outlet />,
})
