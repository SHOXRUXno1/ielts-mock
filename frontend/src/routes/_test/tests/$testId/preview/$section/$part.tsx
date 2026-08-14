import { createFileRoute, redirect } from '@tanstack/react-router'
import { SectionContent } from '@/features/tests/take/section-content'

export const Route = createFileRoute(
  '/_test/tests/$testId/preview/$section/$part',
)({
  beforeLoad: ({ params }) => {
    if (params.section === 'speaking') {
      throw redirect({
        to: '/tests/$testId/preview/$section',
        params: {
          testId: params.testId,
          section: 'speaking',
        },
        replace: true,
      })
    }
    const n = parseInt(params.part, 10)
    if (!Number.isFinite(n) || n < 1) {
      throw redirect({
        to: '/tests/$testId/preview/$section/$part',
        params: {
          testId: params.testId,
          section: params.section,
          part: '1',
        },
        replace: true,
      })
    }
  },
  component: SectionContent,
})
