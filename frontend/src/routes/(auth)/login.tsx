import { createFileRoute } from '@tanstack/react-router'
import { StudentLogin } from '@/features/auth/student-login'

export const Route = createFileRoute('/(auth)/login')({
  component: StudentLogin,
})
