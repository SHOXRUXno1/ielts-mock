import { createFileRoute } from '@tanstack/react-router'
import { TestsImport } from '@/features/tests/import-test'

export const Route = createFileRoute('/_authenticated/tests/import')({
  component: TestsImport,
})
