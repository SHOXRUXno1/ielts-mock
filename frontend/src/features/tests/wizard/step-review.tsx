import { AlertCircle, CheckCircle2, Headphones, BookOpen, PenLine, Mic } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { countScoringSlots, type Question, type Section, type Test } from '../data/schema'

type Props = {
  test: Test
  sections: Section[]
  questionsMap: Record<string, Question[]>
}

type SectionSummary = {
  type: string
  count: number
  questions: number
  warnings: string[]
}

function sectionSlotCount(section: Section, questionsMap: Record<string, Question[]>): number {
  const qs = questionsMap[section.id] ?? []
  if (qs.length > 0) return countScoringSlots(qs)
  return section.question_count ?? 0
}

function summarise(sections: Section[], questionsMap: Record<string, Question[]>): SectionSummary[] {
  const types = ['listening', 'reading', 'writing', 'speaking'] as const
  return types.map((type) => {
    const ofType = sections.filter((s) => s.type === type).sort((a, b) => a.order - b.order)
    const totalQ = ofType.reduce((acc, s) => acc + sectionSlotCount(s, questionsMap), 0)
    const warnings: string[] = []

    if (type === 'listening') {
      if (ofType.length === 0) warnings.push('No listening parts added')
      else if (totalQ === 0) warnings.push('No listening questions')
      else if (totalQ < 40) warnings.push(`Only ${totalQ} listening questions (recommended: 40)`)
    }
    if (type === 'reading') {
      if (ofType.length === 0) warnings.push('No reading passages added')
      else if (totalQ === 0) warnings.push('No reading questions')
      else {
        ofType.forEach((s, i) => {
          const qCount = sectionSlotCount(s, questionsMap)
          if (qCount < 10) warnings.push(`Passage ${i + 1} has only ${qCount} questions (recommended: 13-14)`)
        })
      }
    }
    if (type === 'writing') {
      const q = ofType.reduce((acc, s) => acc + (questionsMap[s.id]?.length ?? s.question_count), 0)
      if (q < 2) warnings.push('Writing needs Task 1 and Task 2')
    }

    return { type, count: ofType.length, questions: totalQ, warnings }
  })
}

const TYPE_META = {
  listening: { label: 'Listening', icon: Headphones, aiManaged: false },
  reading: { label: 'Reading', icon: BookOpen, aiManaged: false },
  writing: { label: 'Writing', icon: PenLine, aiManaged: false },
  speaking: { label: 'Speaking', icon: Mic, aiManaged: true },
}

export function StepReview({ test, sections, questionsMap }: Props) {
  const summaries = summarise(sections, questionsMap)
  const allWarnings = summaries.flatMap((s) => s.warnings)
  const isPublishable = allWarnings.filter((w) => !w.toLowerCase().includes('recommended')).length === 0

  return (
    <div className='space-y-5'>
      {/* Test info */}
      <div className='rounded-lg border border-border bg-muted/50 p-4'>
        <div className='flex items-center gap-2'>
          <h3 className='text-base font-semibold text-foreground'>{test.title}</h3>
          <Badge variant={test.is_published ? 'default' : 'secondary'}>
            {test.is_published ? 'Published' : 'Draft'}
          </Badge>
        </div>
        {test.book_name && (
          <p className='mt-0.5 text-sm text-muted-foreground'>{test.book_name}</p>
        )}
        <p className='mt-0.5 text-xs text-muted-foreground capitalize'>{test.type}</p>
      </div>

      {/* Section summaries */}
      <div className='space-y-2'>
        {summaries.map(({ type, count, questions, warnings }) => {
          const { label, icon: Icon, aiManaged } = TYPE_META[type as keyof typeof TYPE_META]
          const ok = warnings.length === 0
          return (
            <div
              key={type}
              className={cn(
                'flex items-start gap-3 rounded-md border p-3',
                ok ? 'border-border' : 'border-warning/40 bg-warning/5',
              )}
            >
              <div className='mt-0.5'>
                {ok ? (
                  <CheckCircle2 className='size-4 text-success-foreground' />
                ) : (
                  <AlertCircle className='size-4 text-warning-foreground' />
                )}
              </div>
              <div className='flex-1'>
                <div className='flex items-center gap-2'>
                  <Icon className='size-3.5 text-muted-foreground' />
                  <span className='text-sm font-medium text-foreground'>{label}</span>
                  {aiManaged && (
                    <span className='text-xs text-muted-foreground'>— managed by AI Examiner</span>
                  )}
                </div>
                {!aiManaged && (
                  <p className='mt-0.5 text-xs text-muted-foreground'>
                    {count} {count === 1 ? 'section' : 'sections'} · {questions} questions
                  </p>
                )}
                {warnings.map((w, i) => (
                  <p key={i} className='mt-0.5 text-xs text-warning-foreground'>⚠ {w}</p>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {!isPublishable && (
        <Alert>
          <AlertCircle className='size-4' />
          <AlertDescription>
            There are warnings above. You can still publish — you'll be asked to confirm.
          </AlertDescription>
        </Alert>
      )}

      {test.is_published && (
        <Alert>
          <CheckCircle2 className='size-4' />
          <AlertDescription>This test is already published and visible to students.</AlertDescription>
        </Alert>
      )}
    </div>
  )
}

export { type Props as StepReviewProps }
