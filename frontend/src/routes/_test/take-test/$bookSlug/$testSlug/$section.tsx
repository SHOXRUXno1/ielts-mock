import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { Loader2, AlertCircle } from 'lucide-react'
import { fetchTestBySlug } from '@/lib/api/tests'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { TakeTest } from '@/features/tests/take-test'

const searchSchema = z.object({
  resume: z.string().optional(),
})

export const Route = createFileRoute('/_test/take-test/$bookSlug/$testSlug/$section')({
  validateSearch: searchSchema,
  component: SlugTestSection,
})

function SlugTestSection() {
  const { bookSlug, testSlug, section } = Route.useParams()
  const { resume } = Route.useSearch()
  const testNumber = parseInt(testSlug.replace(/^test-/i, ''), 10)

  const { data: test, isLoading, isError } = useQuery({
    queryKey: ['test-by-slug', bookSlug, testNumber],
    queryFn: () => fetchTestBySlug(bookSlug, testNumber),
    enabled: !isNaN(testNumber),
  })

  if (isLoading || !test) {
    return (
      <div className='flex h-screen items-center justify-center bg-white'>
        <Loader2 className='size-8 animate-spin text-slate-400' />
      </div>
    )
  }

  if (isError) {
    return (
      <div className='flex h-screen items-center justify-center bg-white'>
        <Alert variant='destructive' className='max-w-md'>
          <AlertCircle className='size-4' />
          <AlertDescription>Test not found.</AlertDescription>
        </Alert>
      </div>
    )
  }

  return <TakeTest testId={String(test.id)} resume={resume} initialSection={section} />
}
