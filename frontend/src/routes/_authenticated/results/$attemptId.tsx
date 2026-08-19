import { createFileRoute } from '@tanstack/react-router'
import { ResultDetail } from '@/features/results/result-detail'
import { parseResultSearch } from '@/features/results/lib/tabs'

export const Route = createFileRoute('/_authenticated/results/$attemptId')({
  validateSearch: parseResultSearch,
  component: ResultDetail,
})
