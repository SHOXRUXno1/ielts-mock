import { createFileRoute, redirect } from '@tanstack/react-router'
import { SectionContent } from '@/features/tests/take/section-content'

/**
 * /speaking → content (no part index).
 * /listening|reading|writing → redirect to /1
 */
export const Route = createFileRoute(
  '/_test/take-test/$bookSlug/$testSlug/$section/',
)({
  beforeLoad: ({ params, search }) => {
    if (params.section === 'speaking') return
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
  },
  component: SectionContent,
})
