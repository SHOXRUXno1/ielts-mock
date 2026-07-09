import { createFileRoute } from '@tanstack/react-router'
import { z } from 'zod'
import { SpeakingExaminer } from '@/features/speaking-examiner'

export const Route = createFileRoute('/_authenticated/speaking-examiner')({
  validateSearch: z.object({
    attemptId: z.string().uuid().optional(),
  }),
  component: SpeakingExaminer,
})
