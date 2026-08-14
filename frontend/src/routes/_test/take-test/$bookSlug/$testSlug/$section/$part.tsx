import { createFileRoute, redirect } from '@tanstack/react-router'
import { SectionContent } from '@/features/tests/take/section-content'

export const Route = createFileRoute(
  '/_test/take-test/$bookSlug/$testSlug/$section/$part',
)({
  beforeLoad: ({ params, search }) => {
    // Speaking has no part in the URL — collapse /speaking/1 → /speaking
    if (params.section === 'speaking') {
      throw redirect({
        to: '/take-test/$bookSlug/$testSlug/$section',
        params: {
          bookSlug: params.bookSlug,
          testSlug: params.testSlug,
          section: 'speaking',
        },
        search,
        replace: true,
      })
    }
    const n = parseInt(params.part, 10)
    if (!Number.isFinite(n) || n < 1) {
      throw redirect({
        to: '/take-test/$bookSlug/$testSlug/$section/$part',
        params: {
          bookSlug: params.bookSlug,
          testSlug: params.testSlug,
          section: params.section,
          part: '1',
        },
        search,
        replace: true,
      })
    }
  },
  component: SectionContent,
})
