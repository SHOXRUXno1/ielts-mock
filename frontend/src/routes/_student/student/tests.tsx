import { createFileRoute } from '@tanstack/react-router'
import { StudentTests } from '@/features/student/tests'

export const Route = createFileRoute('/_student/student/tests')({
  component: StudentTests,
})
