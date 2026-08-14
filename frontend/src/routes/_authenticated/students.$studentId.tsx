import { createFileRoute } from '@tanstack/react-router'
import { StudentResultDetail } from '@/features/results/student-detail'
import { StudentsDialogs } from '@/features/students/components/students-dialogs'
import { StudentsProvider, useStudents } from '@/features/students/components/students-provider'

export const Route = createFileRoute('/_authenticated/students/$studentId')({
  component: StudentsStudentDetailPage,
})

function StudentsStudentDetailPage() {
  return (
    <StudentsProvider>
      <StudentProfileContent />
      <StudentsDialogs />
    </StudentsProvider>
  )
}

function StudentProfileContent() {
  const { studentId } = Route.useParams()
  const { setOpen, setCurrentRow } = useStudents()

  return (
    <StudentResultDetail
      studentId={studentId}
      backTo='/students'
      backLabel='Back to Students'
      onEdit={(student) => {
        setCurrentRow(student)
        setOpen('edit')
      }}
    />
  )
}
