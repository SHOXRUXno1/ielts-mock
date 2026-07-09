import { createFileRoute } from '@tanstack/react-router'
import { TestDetail } from '@/features/tests/test-detail'

export const Route = createFileRoute('/_authenticated/tests/$testId/')({
  component: TestDetail,
})
