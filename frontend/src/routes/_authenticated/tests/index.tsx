import { createFileRoute } from '@tanstack/react-router'
import { Tests } from '@/features/tests'

export const Route = createFileRoute('/_authenticated/tests/')({
  component: Tests,
})
