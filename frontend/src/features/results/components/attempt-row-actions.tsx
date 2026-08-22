import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { Download, Eye, Loader2, MoreHorizontal, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { deleteAttempt, downloadResultPdf } from '@/lib/api/attempts'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

type Props = {
  attemptId: string
  /** Attempt status — used to disable PDF for attempts with no scores yet. */
  status?: string
  /** Extra query keys to invalidate after mutations */
  invalidateKeys?: unknown[][]
}

export function AttemptRowActions({ attemptId, status, invalidateKeys = [['results']] }: Props) {
  const queryClient = useQueryClient()
  const [deleteOpen, setDeleteOpen] = useState(false)

  const invalidate = () => {
    for (const key of invalidateKeys) {
      void queryClient.invalidateQueries({ queryKey: key })
    }
  }

  const deleteMutation = useMutation({
    mutationFn: () => deleteAttempt(attemptId),
    onSuccess: () => {
      toast.success('Attempt deleted')
      setDeleteOpen(false)
      invalidate()
    },
    onError: () => toast.error('Failed to delete attempt'),
  })

  const pdfMutation = useMutation({
    mutationFn: () => downloadResultPdf(attemptId),
    onError: () => toast.error('Could not generate the PDF'),
  })

  const pdfDisabled = status === 'in_progress'
  const busy = deleteMutation.isPending || pdfMutation.isPending

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant='ghost'
            size='sm'
            className='h-8 w-8 p-0'
            disabled={busy}
            aria-label='Actions'
          >
            {busy ? (
              <Loader2 className='size-4 animate-spin' />
            ) : (
              <MoreHorizontal className='size-4' />
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align='end' className='w-44'>
          <DropdownMenuItem asChild>
            <Link to='/results/$attemptId' params={{ attemptId }}>
              <Eye className='mr-2 size-4' />
              View details
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem
            disabled={pdfDisabled || pdfMutation.isPending}
            onSelect={(e) => {
              e.preventDefault()
              if (pdfDisabled || pdfMutation.isPending) return
              pdfMutation.mutate()
            }}
          >
            {pdfMutation.isPending ? (
              <Loader2 className='mr-2 size-4 animate-spin' />
            ) : (
              <Download className='mr-2 size-4' />
            )}
            Download PDF
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className='text-red-600 focus:text-red-600'
            onClick={() => setDeleteOpen(true)}
          >
            <Trash2 className='mr-2 size-4' />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this attempt permanently?</AlertDialogTitle>
            <AlertDialogDescription>
              This cannot be undone. All answers and evaluation data for this attempt will be removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteMutation.isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className='bg-red-600 hover:bg-red-700'
              disabled={deleteMutation.isPending}
              onClick={(e) => {
                e.preventDefault()
                deleteMutation.mutate()
              }}
            >
              {deleteMutation.isPending && <Loader2 className='mr-2 size-4 animate-spin' />}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
