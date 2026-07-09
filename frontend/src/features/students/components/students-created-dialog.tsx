import { useState } from 'react'
import { CheckCircle, Copy, Check } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { useStudents } from './students-provider'

export function StudentsCreatedDialog() {
  const { open, setOpen, credentials } = useStudents()
  const [copied, setCopied] = useState(false)

  if (!credentials) return null

  const handleCopy = () => {
    const text = `Login: ${credentials.login}\nPassword: ${credentials.password}`
    void navigator.clipboard.writeText(text)
    setCopied(true)
    toast.success('Credentials copied!')
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Dialog open={open === 'show-credentials'} onOpenChange={(v) => !v && setOpen(null)}>
      <DialogContent className='max-w-sm'>
        <DialogHeader>
          <DialogTitle className='flex items-center gap-2'>
            <CheckCircle className='text-green-500' size={20} />
            Student Created!
          </DialogTitle>
        </DialogHeader>

        <div className='space-y-3 rounded-lg border bg-muted/40 p-4'>
          <div>
            <p className='text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1'>Login</p>
            <p className='font-mono text-sm font-semibold'>{credentials.login}</p>
          </div>
          <div>
            <p className='text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1'>Password</p>
            <p className='font-mono text-sm font-semibold'>{credentials.password}</p>
          </div>
        </div>

        <p className='text-xs text-muted-foreground text-center'>
          Save this password — it won't be shown again.
        </p>

        <DialogFooter className='gap-2'>
          <Button variant='outline' onClick={handleCopy} className='flex-1'>
            {copied ? <Check size={14} className='mr-1' /> : <Copy size={14} className='mr-1' />}
            {copied ? 'Copied!' : 'Copy Credentials'}
          </Button>
          <Button onClick={() => setOpen(null)} className='flex-1'>
            Done
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
