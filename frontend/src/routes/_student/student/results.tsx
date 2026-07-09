import { createFileRoute } from '@tanstack/react-router'
import { StudentResults } from '@/features/student/results'

export const Route = createFileRoute('/_student/student/results')({
  component: StudentResults,
})
