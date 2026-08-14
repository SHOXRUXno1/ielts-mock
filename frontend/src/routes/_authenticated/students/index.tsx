import { createFileRoute } from '@tanstack/react-router'
import { Students } from '@/features/students'

export const Route = createFileRoute('/_authenticated/students/')({
  validateSearch: (s: Record<string, unknown>): { q?: string } =>
    typeof s.q === 'string' ? { q: s.q } : {},
  component: Students,
})
