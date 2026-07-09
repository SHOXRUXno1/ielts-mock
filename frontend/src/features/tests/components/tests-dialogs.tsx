import { TestsActionDialog } from './tests-action-dialog'
import { TestsDeleteDialog } from './tests-delete-dialog'
import { useTests } from './tests-provider'

export function TestsDialogs() {
  const { open, setOpen, currentRow, setCurrentRow } = useTests()

  const close = () => {
    setOpen(null)
    // delay clearing so closing animation doesn't flicker
    setTimeout(() => setCurrentRow(null), 300)
  }

  return (
    <>
      <TestsActionDialog
        key='test-add'
        open={open === 'add'}
        onOpenChange={(o) => (o ? setOpen('add') : close())}
      />

      {currentRow && (
        <>
          <TestsActionDialog
            key={`test-edit-${currentRow.id}`}
            currentRow={currentRow}
            open={open === 'edit'}
            onOpenChange={(o) => (o ? setOpen('edit') : close())}
          />

          <TestsDeleteDialog
            key={`test-delete-${currentRow.id}`}
            currentRow={currentRow}
            open={open === 'delete'}
            onOpenChange={(o) => (o ? setOpen('delete') : close())}
          />
        </>
      )}
    </>
  )
}
