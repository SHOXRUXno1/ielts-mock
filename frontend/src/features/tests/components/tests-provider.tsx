import React, { useState } from 'react'
import useDialogState from '@/hooks/use-dialog-state'
import { type Test } from '../data/schema'

type TestsDialogType = 'add' | 'edit' | 'delete'

type TestsContextType = {
  open: TestsDialogType | null
  setOpen: (str: TestsDialogType | null) => void
  currentRow: Test | null
  setCurrentRow: React.Dispatch<React.SetStateAction<Test | null>>
}

const TestsContext = React.createContext<TestsContextType | null>(null)

export function TestsProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useDialogState<TestsDialogType>(null)
  const [currentRow, setCurrentRow] = useState<Test | null>(null)

  return (
    <TestsContext value={{ open, setOpen, currentRow, setCurrentRow }}>
      {children}
    </TestsContext>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export const useTests = () => {
  const ctx = React.useContext(TestsContext)
  if (!ctx) {
    throw new Error('useTests has to be used within <TestsProvider>')
  }
  return ctx
}
