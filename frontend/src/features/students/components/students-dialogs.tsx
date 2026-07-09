import { StudentsActionDialog } from './students-action-dialog'
import { StudentsCreatedDialog } from './students-created-dialog'
import { StudentsDeleteDialog } from './students-delete-dialog'
import { StudentsResetPasswordDialog } from './students-reset-password-dialog'

export function StudentsDialogs() {
  return (
    <>
      <StudentsActionDialog />
      <StudentsCreatedDialog />
      <StudentsDeleteDialog />
      <StudentsResetPasswordDialog />
    </>
  )
}
