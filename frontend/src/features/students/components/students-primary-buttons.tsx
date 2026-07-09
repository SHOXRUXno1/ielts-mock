import { UserPlus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useStudents } from './students-provider'

export function StudentsPrimaryButtons() {
  const { setOpen } = useStudents()
  return (
    <Button onClick={() => setOpen('add')}>
      <UserPlus />
      Add Student
    </Button>
  )
}
