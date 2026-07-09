import { createFileRoute } from '@tanstack/react-router'
import { Students } from '@/features/students'

export const Route = createFileRoute('/_authenticated/students/')({
  component: Students,
})
