import { createFileRoute } from '@tanstack/react-router'
import { TestWizard } from '@/features/tests/wizard'

export const Route = createFileRoute('/_authenticated/tests/$testId/edit')({
  component: EditTestPage,
})

function EditTestPage() {
  const { testId } = Route.useParams()
  return <TestWizard testId={testId} />
}
