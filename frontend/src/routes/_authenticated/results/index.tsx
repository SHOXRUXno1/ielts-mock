import { createFileRoute } from '@tanstack/react-router'
import { Results } from '@/features/results'

export const Route = createFileRoute('/_authenticated/results/')({
  component: Results,
})
