import { createFileRoute } from '@tanstack/react-router'
import { z } from 'zod'
import { SectionContent } from '@/features/tests/take/section-content'
import { TakeTestShell } from '@/features/tests/take/take-test-shell'

const searchSchema = z.object({
  resume: z.string().optional(),
  section: z.string().optional(),
  part: z.string().optional(),
})

export const Route = createFileRoute('/_test/take-test/$testId')({
  validateSearch: searchSchema,
  component: UuidTake,
})

/**
 * Student (and UUID) exam URL. One path segment — no Cambridge slug.
 * Section/part live in the query string so this route does not clash with
 * /take-test/$bookSlug/$testSlug.
 */
function UuidTake() {
  const { testId } = Route.useParams()
  const { resume, section } = Route.useSearch()
  return (
    <TakeTestShell mode='live' testId={testId} resume={resume}>
      {section ? <SectionContent /> : null}
    </TakeTestShell>
  )
}
