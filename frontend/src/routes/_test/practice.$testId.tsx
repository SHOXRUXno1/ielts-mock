import { createFileRoute, redirect } from '@tanstack/react-router'
import { z } from 'zod'
import { SectionContent } from '@/features/tests/take/section-content'
import { TakeTestShell } from '@/features/tests/take/take-test-shell'
import type { SectionType } from '@/features/tests/data/schema'
import { isSectionType } from '@/features/tests/lib/part-resolver'

const searchSchema = z.object({
  attempt: z.string().uuid(),
  scope: z.enum(['part', 'section']).catch('part'),
  section: z.string(),
  part: z.string().optional(),
})

export const Route = createFileRoute('/_test/practice/$testId')({
  validateSearch: searchSchema,
  beforeLoad: ({ search }) => {
    if (!isSectionType(search.section)) {
      throw redirect({ to: '/student/tests' })
    }
  },
  component: UuidPractice,
})

function UuidPractice() {
  const { testId } = Route.useParams()
  const search = Route.useSearch()
  const partNumber = Math.max(1, parseInt(search.part ?? '1', 10) || 1)
  const sectionType = search.section as SectionType
  return (
    <TakeTestShell
      mode='practice'
      testId={testId}
      resume={search.attempt}
      practiceSectionType={sectionType}
      practicePartNumber={partNumber}
      practiceScope={search.scope}
    >
      <SectionContent />
    </TakeTestShell>
  )
}
