import { createFileRoute } from '@tanstack/react-router'
import { ResultDetail } from '@/features/results/result-detail'

export const Route = createFileRoute('/_authenticated/results/$attemptId')({
  component: ResultDetail,
})
