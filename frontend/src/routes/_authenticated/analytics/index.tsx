import { createFileRoute } from '@tanstack/react-router'
import { Analytics } from '@/features/analytics'

export const Route = createFileRoute('/_authenticated/analytics/')({
  validateSearch: (s: Record<string, unknown>): { days?: number } =>
    typeof s.days === 'number' ? { days: s.days } : {},
  component: Analytics,
})
