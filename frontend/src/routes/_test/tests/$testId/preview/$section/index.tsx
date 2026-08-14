import { createFileRoute, redirect } from '@tanstack/react-router'
import { SectionContent } from '@/features/tests/take/section-content'

export const Route = createFileRoute(
  '/_test/tests/$testId/preview/$section/',
)({
  beforeLoad: ({ params }) => {
    if (params.section === 'speaking') return
    throw redirect({
      to: '/tests/$testId/preview/$section/$part',
      params: {
        testId: params.testId,
        section: params.section,
        part: '1',
      },
      replace: true,
    })
  },
  component: SectionContent,
})
