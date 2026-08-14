import { createFileRoute } from '@tanstack/react-router'
import { z } from 'zod'
import { TakeTestShell } from '@/features/tests/take/take-test-shell'

const searchSchema = z.object({
  resume: z.string().optional(),
})

export const Route = createFileRoute('/_test/take-test/$bookSlug/$testSlug')({
  validateSearch: searchSchema,
  component: LiveTakeShell,
})

function LiveTakeShell() {
  const { bookSlug, testSlug } = Route.useParams()
  const { resume } = Route.useSearch()
  return (
    <TakeTestShell
      mode='live'
      bookSlug={bookSlug}
      testSlug={testSlug}
      resume={resume}
    />
  )
}
