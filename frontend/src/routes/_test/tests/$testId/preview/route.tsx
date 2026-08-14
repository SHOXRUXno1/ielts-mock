import { createFileRoute } from '@tanstack/react-router'
import { z } from 'zod'
import { TakeTestShell } from '@/features/tests/take/take-test-shell'

const searchSchema = z.object({
  /** Legacy query from admin links — index redirects into path. */
  section: z.string().optional(),
})

export const Route = createFileRoute('/_test/tests/$testId/preview')({
  validateSearch: searchSchema,
  component: PreviewShell,
})

function PreviewShell() {
  const { testId } = Route.useParams()
  return <TakeTestShell mode='preview' testId={testId} />
}
