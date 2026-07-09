import { createFileRoute } from '@tanstack/react-router'
import { StudentDashboard } from '@/features/student/dashboard'

export const Route = createFileRoute('/_student/student/dashboard')({
  component: StudentDashboard,
})
