import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Check, Copy } from 'lucide-react'
import { toast } from 'sonner'
import { resetStudentPassword } from '@/lib/api/students'
import { apiErrorMessage } from '@/lib/api/error'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog'
import { useStudents } from './students-provider'

export function StudentsResetPasswordDialog() {
  const { open, setOpen, currentRow } = useStudents()
  const [newPassword, setNewPassword] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const mutation = useMutation({
    mutationFn: () => resetStudentPassword(currentRow!.id),
    onSuccess: (data) => {
      setNewPassword(data.password)
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Failed to reset password.')),
  })

  const handleClose = () => {
    setOpen(null)
    setNewPassword(null)
    setCopied(false)
  }

  const handleCopy = () => {
    if (!newPassword) return
    void navigator.clipboard.writeText(newPassword)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Dialog open={open === 'reset-password'} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className='max-w-sm'>
        <DialogHeader>
          <DialogTitle>Reset Password</DialogTitle>
          <DialogDescription>
            Generate a new password for {currentRow?.full_name}.
          </DialogDescription>
        </DialogHeader>

        {newPassword ? (
          <>
            <div className='rounded-lg border bg-muted/40 p-4'>
              <p className='text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1'>New Password</p>
              <p className='font-mono text-sm font-semibold'>{newPassword}</p>
            </div>
            <p className='text-xs text-muted-foreground text-center'>
              Save this password — it won't be shown again.
            </p>
            <DialogFooter className='gap-2'>
              <Button variant='outline' onClick={handleCopy} className='flex-1'>
                {copied ? <Check size={14} className='mr-1' /> : <Copy size={14} className='mr-1' />}
                {copied ? 'Copied!' : 'Copy Password'}
              </Button>
              <Button onClick={handleClose} className='flex-1'>Done</Button>
            </DialogFooter>
          </>
        ) : (
          <DialogFooter>
            <Button variant='outline' onClick={handleClose}>Cancel</Button>
            <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
              {mutation.isPending ? 'Generating…' : 'Generate New Password'}
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  )
}
