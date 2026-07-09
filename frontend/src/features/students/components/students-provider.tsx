import { createContext, useContext, useState } from 'react'
import type { Student, StudentDialogAction } from '../data/schema'

interface StudentsContextValue {
  open: StudentDialogAction
  setOpen: (action: StudentDialogAction) => void
  currentRow: Student | null
  setCurrentRow: (row: Student | null) => void
  credentials: { login: string; password: string } | null
  setCredentials: (c: { login: string; password: string } | null) => void
}

const StudentsContext = createContext<StudentsContextValue | null>(null)

export function StudentsProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState<StudentDialogAction>(null)
  const [currentRow, setCurrentRow] = useState<Student | null>(null)
  const [credentials, setCredentials] = useState<{ login: string; password: string } | null>(null)

  return (
    <StudentsContext.Provider value={{ open, setOpen, currentRow, setCurrentRow, credentials, setCredentials }}>
      {children}
    </StudentsContext.Provider>
  )
}

export function useStudents() {
  const ctx = useContext(StudentsContext)
  if (!ctx) throw new Error('useStudents must be used within StudentsProvider')
  return ctx
}
