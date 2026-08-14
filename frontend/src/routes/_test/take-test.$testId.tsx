import { useEffect } from 'react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { Loader2 } from 'lucide-react'
import { fetchSlugRedirect } from '@/lib/api/tests'

const searchSchema = z.object({
  resume: z.string().optional(),
})

export const Route = createFileRoute('/_test/take-test/$testId')({
  validateSearch: searchSchema,
  component: UuidRedirect,
})

/**
 * Backward-compat redirect:
 * /take-test/:uuid → /take-test/:bookSlug/:testSlug/listening/1
 */
function UuidRedirect() {
  const { testId } = Route.useParams()
  const { resume } = Route.useSearch()
  const navigate = useNavigate()

  const { data, isError, error } = useQuery({
    queryKey: ['slug-redirect', testId],
    queryFn: () => fetchSlugRedirect(testId),
    retry: false,
  })

  useEffect(() => {
    if (!data) return
    void navigate({
      to: '/take-test/$bookSlug/$testSlug/$section/$part',
      params: {
        bookSlug: data.book_slug,
        testSlug: `test-${data.test_number}`,
        section: 'listening',
        part: '1',
      },
      search: resume ? { resume } : {},
      replace: true,
    })
  }, [data, navigate, resume])

  if (isError) {
    const status = (error as { response?: { status?: number } })?.response
      ?.status
    return (
      <div className='flex h-screen items-center justify-center bg-white px-4'>
        <p className='text-sm text-slate-600'>
          {status === 403
            ? 'This test is not available. It may be unpublished.'
            : status === 404
              ? 'Test not found.'
              : 'Failed to open test. Please try again.'}
        </p>
      </div>
    )
  }

  return (
    <div className='flex h-screen items-center justify-center bg-white'>
      <Loader2 className='size-8 animate-spin text-slate-400' />
    </div>
  )
}
