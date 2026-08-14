import { createFileRoute, Outlet, redirect } from '@tanstack/react-router'
import { isSectionType } from '@/features/tests/lib/part-resolver'

export const Route = createFileRoute(
  '/_test/tests/$testId/preview/$section',
)({
  beforeLoad: ({ params }) => {
    if (!isSectionType(params.section)) {
      throw redirect({
        to: '/tests/$testId/preview/$section/$part',
        params: {
          testId: params.testId,
          section: 'listening',
          part: '1',
        },
        replace: true,
      })
    }
  },
  component: () => <Outlet />,
})
