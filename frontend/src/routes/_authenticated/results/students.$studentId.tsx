import { createFileRoute } from '@tanstack/react-router'
import { StudentResultDetail } from '@/features/results/student-detail'

export const Route = createFileRoute('/_authenticated/results/students/$studentId')({
  component: StudentResultDetailPage,
})

function StudentResultDetailPage() {
  const { studentId } = Route.useParams()
  return (
    <StudentResultDetail
      studentId={studentId}
      backTo='/results'
      backLabel='Back to Results'
    />
  )
}
