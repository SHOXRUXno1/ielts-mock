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
 * Backward-compat redirect: /take-test/:uuid → /take-test/:bookSlug/:testSlug
 *
 * Old bookmarked or shared UUID-based URLs will land here and be transparently
 * redirected to the canonical slug URL.
 */
function UuidRedirect() {
  const { testId } = Route.useParams()
  const { resume } = Route.useSearch()
  const navigate = useNavigate()

  const { data } = useQuery({
    queryKey: ['slug-redirect', testId],
    queryFn: () => fetchSlugRedirect(testId),
    retry: false,
  })

  useEffect(() => {
    if (!data) return
    void navigate({
      to: '/take-test/$bookSlug/$testSlug',
      params: {
        bookSlug: data.book_slug,
        testSlug: `test-${data.test_number}`,
      },
      search: resume ? { resume } : {},
      replace: true,
    })
  }, [data, navigate, resume])

  return (
    <div className='flex h-screen items-center justify-center bg-white'>
      <Loader2 className='size-8 animate-spin text-slate-400' />
    </div>
  )
}
