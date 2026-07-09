import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { deleteTest } from '@/lib/api/tests'
import { ConfirmDialog } from '@/components/confirm-dialog'
import { type Test } from '../data/schema'

type TestsDeleteDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  currentRow: Test
}

export function TestsDeleteDialog({
  open,
  onOpenChange,
  currentRow,
}: TestsDeleteDialogProps) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => deleteTest(currentRow.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests'] })
      toast.success(`"${currentRow.title}" deleted`)
      onOpenChange(false)
    },
  })

  return (
    <ConfirmDialog
      open={open}
      onOpenChange={onOpenChange}
      destructive
      isLoading={mutation.isPending}
      handleConfirm={() => mutation.mutate()}
      title='Delete test'
      desc={
        <>
          Are you sure you want to delete{' '}
          <span className='font-semibold'>{currentRow.title}</span>? This will
          also delete all sections, questions and student attempts for this
          test. This action cannot be undone.
        </>
      }
      confirmText='Delete'
    />
  )
}
