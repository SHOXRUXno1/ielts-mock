import { useEffect } from 'react'
import { createFileRoute, useNavigate, useSearch } from '@tanstack/react-router'
import { isSectionType } from '@/features/tests/lib/part-resolver'

/** /tests/:id/preview[?section=] → /tests/:id/preview/{section}/1 */
export const Route = createFileRoute('/_test/tests/$testId/preview/')({
  component: PreviewIndex,
})

function PreviewIndex() {
  const { testId } = Route.useParams()
  const { section: legacySection } = useSearch({
    from: '/_test/tests/$testId/preview',
  })
  const navigate = useNavigate()

  useEffect(() => {
    const section =
      legacySection && isSectionType(legacySection)
        ? legacySection
        : 'listening'
    if (section === 'speaking') {
      void navigate({
        to: '/tests/$testId/preview/$section',
        params: { testId, section: 'speaking' },
        replace: true,
      })
      return
    }
    void navigate({
      to: '/tests/$testId/preview/$section/$part',
      params: { testId, section, part: '1' },
      replace: true,
    })
  }, [testId, legacySection, navigate])

  return null
}
