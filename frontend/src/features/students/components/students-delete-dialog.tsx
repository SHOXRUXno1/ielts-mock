import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { deleteStudent } from '@/lib/api/students'
import { apiErrorMessage } from '@/lib/api/error'
import { Button } from '@/components/ui/button'
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
} from '@/components/ui/alert-dialog'
import { useStudents } from './students-provider'

export function StudentsDeleteDialog() {
  const { open, setOpen, currentRow } = useStudents()
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => deleteStudent(currentRow!.id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['students'] })
      setOpen(null)
      toast.success('Student deleted.')
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Failed to delete student.')),
  })

  return (
    <AlertDialog open={open === 'delete'} onOpenChange={(v) => !v && setOpen(null)}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Student?</AlertDialogTitle>
          <AlertDialogDescription>
            {currentRow?.full_name} ({currentRow?.login}) will be
            deactivated and won't be able to log in. Their test history will be preserved.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <Button
            variant='destructive'
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
          >
            {mutation.isPending ? 'Deleting…' : 'Delete'}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
