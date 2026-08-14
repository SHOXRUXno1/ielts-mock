import { createFileRoute } from '@tanstack/react-router'
import { SectionContent } from '@/features/tests/take/section-content'
import { TakeTestShell } from '@/features/tests/take/take-test-shell'
import type { SectionType } from '@/features/tests/data/schema'
import { isSectionType } from '@/features/tests/lib/part-resolver'

export const Route = createFileRoute(
  '/_test/practice/$bookSlug/$testSlug/$section/$part',
)({
  component: PracticePart,
})

function PracticePart() {
  const { bookSlug, testSlug, section, part } = Route.useParams()
  const search = Route.useSearch()
  const partNumber = Math.max(1, parseInt(part, 10) || 1)
  const sectionType: SectionType = isSectionType(section)
    ? (section as SectionType)
    : 'listening'
  const practiceScope = search.scope === 'section' ? 'section' : 'part'
  return (
    <TakeTestShell
      mode='practice'
      bookSlug={bookSlug}
      testSlug={testSlug}
      resume={search.attempt}
      practiceSectionType={sectionType}
      practicePartNumber={partNumber}
      practiceScope={practiceScope}
    >
      <SectionContent />
    </TakeTestShell>
  )
}
