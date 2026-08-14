import { createFileRoute } from '@tanstack/react-router'
import { StudentProfile } from '@/features/student/profile'

export const Route = createFileRoute('/_student/student/profile')({
  component: StudentProfile,
})
