import { createFileRoute } from '@tanstack/react-router'
import { ReviewScreen } from '@/features/tests/take/review-screen'

export const Route = createFileRoute(
  '/_test/take-test/$bookSlug/$testSlug/review',
)({
  component: ReviewScreen,
})
