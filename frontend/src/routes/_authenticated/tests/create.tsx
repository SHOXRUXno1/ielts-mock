import { createFileRoute } from '@tanstack/react-router'
import { TestWizard } from '@/features/tests/wizard'

export const Route = createFileRoute('/_authenticated/tests/create')({
  component: CreateTestPage,
})

function CreateTestPage() {
  return <TestWizard />
}
