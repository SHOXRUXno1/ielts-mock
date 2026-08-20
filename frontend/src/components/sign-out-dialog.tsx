import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import { ConfirmDialog } from '@/components/confirm-dialog'
import { logout } from '@/lib/api/auth'
import { clearLocalSession, loginReplaceOptions } from '@/lib/sign-out'

interface SignOutDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SignOutDialog({ open, onOpenChange }: SignOutDialogProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const handleSignOut = () => {
    void (async () => {
      try {
        await logout()
      } catch {
        // Network failure must not block local sign-out
      }
      clearLocalSession(queryClient)
      void navigate(loginReplaceOptions)
    })()
  }

  return (
    <ConfirmDialog
      open={open}
      onOpenChange={onOpenChange}
      title='Sign out'
      desc='Are you sure you want to sign out? You will need to sign in again to access your account.'
      confirmText='Sign out'
      destructive
      handleConfirm={handleSignOut}
      className='sm:max-w-sm'
    />
  )
}
