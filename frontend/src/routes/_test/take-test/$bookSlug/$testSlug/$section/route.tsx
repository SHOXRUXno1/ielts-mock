import { createFileRoute, Outlet, redirect } from '@tanstack/react-router'
import { isSectionType } from '@/features/tests/lib/part-resolver'

export const Route = createFileRoute(
  '/_test/take-test/$bookSlug/$testSlug/$section',
)({
  beforeLoad: ({ params, search }) => {
    if (!isSectionType(params.section)) {
      throw redirect({
        to: '/take-test/$bookSlug/$testSlug/$section/$part',
        params: {
          bookSlug: params.bookSlug,
          testSlug: params.testSlug,
          section: 'listening',
          part: '1',
        },
        search,
        replace: true,
      })
    }
  },
  component: () => <Outlet />,
})
