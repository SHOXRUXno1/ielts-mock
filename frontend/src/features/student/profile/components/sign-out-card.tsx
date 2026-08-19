import { LogOut } from 'lucide-react'
import { Panel } from '@/components/report'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { ENTER } from '@/features/results/lib/motion'

type SignOutCardProps = {
  onConfirm: () => void
}

export function SignOutCard({ onConfirm }: SignOutCardProps) {
  return (
    <Panel className={ENTER} padding='sm'>
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button
            variant='outline'
            className='w-full justify-center gap-2 rounded-lg border-destructive/30 text-destructive hover:bg-destructive/10 hover:text-destructive'
          >
            <LogOut className='size-4' />
            Sign out
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Sign out?</AlertDialogTitle>
            <AlertDialogDescription>
              You will need to sign in again to continue your tests and view
              results.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className='bg-destructive text-white hover:bg-destructive/90'
              onClick={onConfirm}
            >
              Sign out
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Panel>
  )
}
