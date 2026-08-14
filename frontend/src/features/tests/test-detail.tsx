import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getRouteApi, Link } from '@tanstack/react-router'
import {
  AlertTriangle,
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  ExternalLink,
  Headphones,
  LayoutGrid,
  Loader2,
  Mic,
  Pencil,
  PenLine,
  Play,
  HelpCircle,
  Upload,
} from 'lucide-react'
import { toast } from 'sonner'
import { fetchQuestions } from '@/lib/api/questions'
import { fetchAdminTest, publishTest } from '@/lib/api/tests'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { PracticePartsEditor } from './components/practice-parts-editor'
import { QuestionList } from './components/question-list'
import { SectionEditDialog } from './components/section-edit-dialog'
import {
  durationByType,
  estimatedTotalMinutes,
  formatMinutes,
  SPEAKING_TYPICAL_MINUTES,
} from './data/duration-rules'
import { type Question, type Section, type SectionSettings, type SectionType, type TestDetail as TestDetailType } from './data/schema'

const route = getRouteApi('/_authenticated/tests/$testId')

// ── Helpers ───────────────────────────────────────────────────────────────────

function sectionLabel(type: SectionType, indexWithinType: number): string {
  switch (type) {
    case 'listening': return `Section ${indexWithinType + 1}`
    case 'reading':   return `Passage ${indexWithinType + 1}`
    case 'writing':   return `Task ${indexWithinType + 1}`
    case 'speaking':  return `Part ${indexWithinType + 1}`
  }
}

const TYPE_ORDER: SectionType[] = ['listening', 'reading', 'writing', 'speaking']

const TYPE_META: Record<
  SectionType,
  { label: string; icon: typeof Headphones; color: string; bg: string }
> = {
  listening: {
    label: 'Listening',
    icon: Headphones,
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-50 dark:bg-blue-950/40',
  },
  reading: {
    label: 'Reading',
    icon: BookOpen,
    color: 'text-emerald-600 dark:text-emerald-400',
    bg: 'bg-emerald-50 dark:bg-emerald-950/40',
  },
  writing: {
    label: 'Writing',
    icon: PenLine,
    color: 'text-violet-600 dark:text-violet-400',
    bg: 'bg-violet-50 dark:bg-violet-950/40',
  },
  speaking: {
    label: 'Speaking',
    icon: Mic,
    color: 'text-amber-600 dark:text-amber-400',
    bg: 'bg-amber-50 dark:bg-amber-950/40',
  },
}

type PublishCheck = {
  errors: string[]
  warnings: string[]
}

function computePublishChecks(
  test: TestDetailType,
  writingQs: Question[],
): PublishCheck {
  const errors: string[] = []
  const warnings: string[] = []
  const isAcademic = (test.type || '').toLowerCase() === 'academic'

  const taskNumbers = new Set(
    writingQs
      .map((q) => q.task_number)
      .filter((n): n is number => n === 1 || n === 2),
  )
  if (writingQs.length !== 2 || taskNumbers.size !== 2 || !taskNumbers.has(1) || !taskNumbers.has(2)) {
    errors.push(
      `Writing must have exactly 2 tasks with task_number 1 and 2 (found ${writingQs.length} question(s)).`,
    )
  }

  const task1 = writingQs.find((q) => q.task_number === 1)
  const task2 = writingQs.find((q) => q.task_number === 2)

  if (isAcademic && task1 && !task1.image_url) {
    errors.push('Academic Writing Task 1 requires a chart/diagram image.')
  }

  for (const q of writingQs) {
    const prompt = String(q.content?.prompt ?? '').trim()
    if (!prompt && q.task_number != null) {
      errors.push(`Writing Task ${q.task_number} is missing a prompt.`)
    }
  }

  if (task2 && !task2.essay_type) {
    warnings.push('Task 2 essay type is not set.')
  }

  return { errors, warnings }
}

function extractPublishErrors(err: unknown): string[] {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response
    ?.data?.detail
  if (detail && typeof detail === 'object' && !Array.isArray(detail) && 'errors' in detail) {
    const errors = (detail as { errors: unknown }).errors
    if (Array.isArray(errors)) return errors.map(String)
  }
  if (typeof detail === 'string') return [detail]
  if (Array.isArray(detail)) {
    return detail.map((d) =>
      typeof d === 'object' && d && 'msg' in d
        ? String((d as { msg: string }).msg)
        : String(d),
    )
  }
  return ['Failed to publish test']
}

// ── Summary strip ─────────────────────────────────────────────────────────────

function SummaryStrip({
  sections,
  sectionSettings,
  isPublished,
}: {
  sections: Section[]
  sectionSettings: SectionSettings[]
  isPublished: boolean
}) {
  const totalQuestions = sections.reduce((s, sec) => s + sec.question_count, 0)
  const totalMinutes = estimatedTotalMinutes(sectionSettings)
  const estimated = durationByType(sectionSettings).speaking == null

  const typeCounts = TYPE_ORDER.reduce<Record<string, number>>((acc, t) => {
    const n = sections.filter((s) => s.type === t).length
    if (n) acc[t] = n
    return acc
  }, {})
  const typeStr = Object.entries(typeCounts)
    .map(([t, n]) => `${n}${t[0].toUpperCase()}`)
    .join(' · ')

  const cards = [
    {
      icon: LayoutGrid,
      label: 'Sections',
      value: sections.length,
      sub: typeStr || '—',
      color: 'text-blue-600 dark:text-blue-400',
      bg: 'bg-blue-500/10',
    },
    {
      icon: HelpCircle,
      label: 'Questions',
      value: totalQuestions,
      sub: 'total',
      color: 'text-emerald-600 dark:text-emerald-400',
      bg: 'bg-emerald-500/10',
    },
    {
      icon: Clock,
      label: 'Duration',
      value: `${estimated ? '~' : ''}${formatMinutes(totalMinutes)}`,
      sub: `${totalMinutes} minutes total`,
      color: 'text-amber-600 dark:text-amber-400',
      bg: 'bg-amber-500/10',
    },
    {
      icon: isPublished ? Play : Pencil,
      label: 'Status',
      value: isPublished ? 'Published' : 'Draft',
      sub: isPublished ? 'visible to students' : 'not visible',
      color: isPublished
        ? 'text-emerald-600 dark:text-emerald-400'
        : 'text-muted-foreground',
      bg: isPublished ? 'bg-emerald-500/10' : 'bg-muted',
    },
  ]

  return (
    <div className='grid grid-cols-2 gap-3 sm:grid-cols-4'>
      {cards.map(({ icon: Icon, label, value, sub, color, bg }) => (
        <div
          key={label}
          className='flex items-center gap-3 rounded-xl border bg-card px-4 py-3'
        >
          <span
            className={`flex size-10 shrink-0 items-center justify-center rounded-lg ${bg}`}
          >
            <Icon className={`size-5 ${color}`} />
          </span>
          <div className='min-w-0'>
            <p className='text-xl font-semibold leading-tight tabular-nums truncate'>
              {value}
            </p>
            <p className='text-xs font-medium text-muted-foreground'>{label}</p>
            <p className='truncate text-xs text-muted-foreground/60'>{sub}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Duration breakdown ────────────────────────────────────────────────────────

function DurationBreakdown({
  sectionSettings,
}: {
  sectionSettings: SectionSettings[]
}) {
  const durations = durationByType(sectionSettings)
  const total = estimatedTotalMinutes(sectionSettings)
  const estimated = durations.speaking == null

  return (
    <div className='rounded-xl border bg-card px-5 py-4'>
      <h3 className='mb-3 flex items-center gap-2 text-sm font-semibold'>
        <Clock className='size-4 text-muted-foreground' />
        Total test duration
      </h3>
      <dl className='space-y-1.5 text-sm'>
        {TYPE_ORDER.map((type) => (
          <div key={type} className='flex justify-between gap-4'>
            <dt className='text-muted-foreground'>{TYPE_META[type].label}</dt>
            <dd className='tabular-nums'>
              {durations[type] != null
                ? `${durations[type]} min`
                : type === 'speaking'
                  ? `~${SPEAKING_TYPICAL_MINUTES} min (AI-paced)`
                  : 'Untimed'}
            </dd>
          </div>
        ))}
        <div className='flex justify-between gap-4 border-t pt-1.5 font-medium'>
          <dt>Total</dt>
          <dd className='tabular-nums'>
            {estimated ? '~' : ''}
            {formatMinutes(total)}
          </dd>
        </div>
      </dl>
    </div>
  )
}

// ── Section row ───────────────────────────────────────────────────────────────

function SectionRow({
  section,
  label,
  isExpanded,
  onToggle,
  onEdit,
  testId,
}: {
  section: Section
  label: string
  isExpanded: boolean
  onToggle: () => void
  onEdit: () => void
  testId: string
}) {
  return (
    <>
      <tr
        className='group cursor-pointer border-b border-border/50 last:border-0 hover:bg-muted/40 transition-colors'
        onClick={onToggle}
      >
        <td className='py-3 pl-5 pr-3 w-8'>
          {isExpanded ? (
            <ChevronDown className='size-4 text-muted-foreground' />
          ) : (
            <ChevronRight className='size-4 text-muted-foreground' />
          )}
        </td>
        <td className='py-3 px-3'>
          <span className='text-sm font-medium'>{label}</span>
        </td>
        <td className='py-3 px-3 text-sm text-muted-foreground tabular-nums'>
          {section.question_count}
        </td>
        <td className='py-3 px-3 text-sm'>
          {section.audio_url ? (
            <a
              href={section.audio_url}
              target='_blank'
              rel='noreferrer'
              onClick={(e) => e.stopPropagation()}
              className='inline-flex items-center gap-1 text-blue-600 hover:underline dark:text-blue-400'
            >
              Open file
              <ExternalLink className='size-3' />
            </a>
          ) : (
            <span className='text-muted-foreground/50'>—</span>
          )}
        </td>
        <td className='py-3 pl-3 pr-5 text-right'>
          <Button
            variant='ghost'
            size='sm'
            className='h-7 px-2 text-xs gap-1'
            onClick={(e) => {
              e.stopPropagation()
              onEdit()
            }}
          >
            <Pencil className='size-3' />
            Edit
          </Button>
        </td>
      </tr>
      {isExpanded && (
        <tr className='border-b border-border/50 last:border-0'>
          <td colSpan={5} className='bg-muted/20 px-5 py-4'>
            <QuestionList
              sectionId={section.id}
              sectionType={section.type}
              testId={testId}
            />
          </td>
        </tr>
      )}
    </>
  )
}

// ── Type group ────────────────────────────────────────────────────────────────

function TypeGroup({
  type,
  sections,
  durationMinutes,
  expandedId,
  onToggle,
  onEdit,
  testId,
}: {
  type: SectionType
  sections: Section[]
  durationMinutes: number | null
  expandedId: string | null
  onToggle: (id: string) => void
  onEdit: (s: Section) => void
  testId: string
}) {
  const meta = TYPE_META[type]
  const Icon = meta.icon
  const totalQ = sections.reduce((s, sec) => s + sec.question_count, 0)
  const durationLabel =
    durationMinutes != null
      ? formatMinutes(durationMinutes)
      : type === 'speaking'
        ? `~${SPEAKING_TYPICAL_MINUTES} min (AI-paced)`
        : 'untimed'

  const sorted = [...sections].sort((a, b) => a.order - b.order)

  return (
    <div>
      <div className='mb-2 flex items-center gap-3'>
        <div className={`rounded-lg p-1.5 ${meta.bg}`}>
          <Icon className={`size-4 ${meta.color}`} />
        </div>
        <div>
          <span className='font-semibold text-sm'>{meta.label}</span>
          <span className='ml-2 text-xs text-muted-foreground'>
            {sections.length} {sections.length === 1 ? 'section' : 'sections'} · {totalQ} questions · {durationLabel}
          </span>
        </div>
      </div>

      <div className='rounded-xl border bg-card overflow-hidden'>
        <table className='w-full'>
          <thead>
            <tr className='border-b bg-muted/30'>
              <th className='py-2 pl-5 pr-3 w-8' />
              <th className='py-2 px-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide'>
                Section
              </th>
              <th className='py-2 px-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide'>
                Questions
              </th>
              <th className='py-2 px-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide'>
                Audio
              </th>
              <th className='py-2 pl-3 pr-5' />
            </tr>
          </thead>
          <tbody>
            {sorted.map((section, i) => (
              <SectionRow
                key={section.id}
                section={section}
                label={sectionLabel(type, i)}
                isExpanded={expandedId === section.id}
                onToggle={() => onToggle(section.id)}
                onEdit={() => onEdit(section)}
                testId={testId}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Publish dialog ────────────────────────────────────────────────────────────

function PublishValidationDialog({
  open,
  onOpenChange,
  checks,
  loading,
  publishing,
  onConfirm,
}: {
  open: boolean
  onOpenChange: (o: boolean) => void
  checks: PublishCheck
  loading: boolean
  publishing: boolean
  onConfirm: (force: boolean) => void
}) {
  const allIssues = [...checks.errors, ...checks.warnings]
  const hasIssues = allIssues.length > 0
  const clean = !loading && !hasIssues

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className='max-w-md'>
        <DialogHeader>
          <DialogTitle>Publish Test</DialogTitle>
          <DialogDescription>
            Review validation results before making this test visible to students.
          </DialogDescription>
        </DialogHeader>

        <div className='space-y-4 py-2'>
          {loading ? (
            <div className='flex items-center justify-center gap-2 py-8 text-sm text-muted-foreground'>
              <Loader2 className='size-4 animate-spin' />
              Checking writing tasks…
            </div>
          ) : (
            <>
              {hasIssues && (
                <div className='space-y-2'>
                  <p className='flex items-center gap-1.5 text-sm font-medium text-amber-700'>
                    <AlertTriangle className='size-4' />
                    Warnings
                  </p>
                  <ul className='space-y-1.5 rounded-md border border-amber-200 bg-amber-50 p-3'>
                    {allIssues.map((w) => (
                      <li key={w} className='text-sm text-amber-800'>
                        {w}
                      </li>
                    ))}
                  </ul>
                  <p className='text-xs text-muted-foreground'>
                    You can still publish. Consider fixing these for a better student experience.
                  </p>
                </div>
              )}

              {clean && (
                <div className='flex items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800'>
                  <CheckCircle2 className='size-4 shrink-0' />
                  All checks passed. Ready to publish.
                </div>
              )}
            </>
          )}
        </div>

        <DialogFooter>
          <Button variant='outline' onClick={() => onOpenChange(false)} disabled={publishing}>
            Cancel
          </Button>
          <Button onClick={() => onConfirm(hasIssues)} disabled={loading || publishing}>
            {publishing && <Loader2 className='mr-1 size-4 animate-spin' />}
            {hasIssues ? 'Publish anyway' : 'Publish'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export function TestDetail() {
  const { testId } = route.useParams()
  const queryClient = useQueryClient()
  const [editingSection, setEditingSection] = useState<Section | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [publishOpen, setPublishOpen] = useState(false)

  const { data: test, isLoading } = useQuery({
    queryKey: ['tests', testId],
    queryFn: () => fetchAdminTest(testId),
  })

  const writingSectionIds =
    test?.sections.filter((s) => s.type === 'writing').map((s) => s.id) ?? []

  const { data: writingQuestions = [], isFetching: writingQsLoading } = useQuery({
    queryKey: ['publish-writing-qs', testId, writingSectionIds],
    queryFn: async () => {
      const all: Question[] = []
      for (const sid of writingSectionIds) {
        all.push(...(await fetchQuestions(sid)))
      }
      return all
    },
    enabled: publishOpen && writingSectionIds.length > 0,
  })

  const publishChecks =
    test && publishOpen && !writingQsLoading
      ? computePublishChecks(test, writingQuestions)
      : { errors: [] as string[], warnings: [] as string[] }

  const publishMutation = useMutation({
    mutationFn: (force: boolean = false) => publishTest(testId, force),
    onSuccess: () => {
      toast.success('Test published')
      setPublishOpen(false)
      void queryClient.invalidateQueries({ queryKey: ['tests', testId] })
      void queryClient.invalidateQueries({ queryKey: ['tests'] })
    },
    onError: (err: unknown) => {
      for (const msg of extractPublishErrors(err)) {
        toast.error(msg)
      }
    },
  })

  function toggleExpanded(id: string) {
    setExpandedId((prev) => (prev === id ? null : id))
  }

  function openEdit(section: Section) {
    setEditingSection(section)
    setDialogOpen(true)
  }

  const groupedSections = test
    ? TYPE_ORDER.reduce<Record<SectionType, Section[]>>(
        (acc, t) => {
          acc[t] = test.sections.filter((s) => s.type === t)
          return acc
        },
        { listening: [], reading: [], writing: [], speaking: [] },
      )
    : null

  return (
    <>
      <Header fixed>
        <Search className='me-auto' />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main className='flex flex-1 flex-col gap-6'>
        <div>
          <Button asChild variant='ghost' size='sm' className='mb-3 -ms-3'>
            <Link to='/tests'>
              <ArrowLeft className='size-4' />
              Back to tests
            </Link>
          </Button>

          {isLoading ? (
            <div className='space-y-2'>
              <div className='h-8 w-48 rounded-lg bg-muted/50 animate-pulse' />
              <div className='h-4 w-64 rounded-lg bg-muted/50 animate-pulse' />
            </div>
          ) : test ? (
            <div className='flex flex-wrap items-start justify-between gap-3'>
              <div>
                <div className='flex items-center gap-2.5'>
                  <h2 className='text-2xl font-bold tracking-tight'>{test.title}</h2>
                  <Badge variant={test.is_published ? 'default' : 'secondary'}>
                    {test.is_published ? 'Published' : 'Draft'}
                  </Badge>
                </div>
                {test.description && (
                  <p className='mt-1 text-sm text-muted-foreground'>{test.description}</p>
                )}
              </div>
              <div className='flex flex-wrap items-center gap-2'>
                <Button asChild variant='outline'>
                  <Link to='/tests/$testId/edit' params={{ testId }}>
                    <Pencil className='size-4' />
                    Edit Test
                  </Link>
                </Button>
                <Button asChild variant='outline'>
                  <Link to='/tests/$testId/preview' params={{ testId }} target='_blank'>
                    <Play className='size-4' />
                    Preview as Student
                  </Link>
                </Button>
                {!test.is_published && (
                  <Button onClick={() => setPublishOpen(true)}>
                    <Upload className='size-4' />
                    Publish
                  </Button>
                )}
              </div>
            </div>
          ) : (
            <p className='text-muted-foreground'>Test not found.</p>
          )}
        </div>

        {test && (
          <SummaryStrip
            sections={test.sections}
            sectionSettings={test.section_settings ?? []}
            isPublished={test.is_published}
          />
        )}

        {test && <DurationBreakdown sectionSettings={test.section_settings ?? []} />}

        {test && groupedSections && (
          <div className='space-y-6'>
            <h3 className='text-lg font-semibold'>Sections</h3>
            {TYPE_ORDER.filter((t) => groupedSections[t].length > 0).map((type) => (
              <TypeGroup
                key={type}
                type={type}
                sections={groupedSections[type]}
                durationMinutes={
                  durationByType(test.section_settings)[type]
                }
                expandedId={expandedId}
                onToggle={toggleExpanded}
                onEdit={openEdit}
                testId={testId}
              />
            ))}
          </div>
        )}

        {test && (
          <PracticePartsEditor
            testId={testId}
            sectionSettings={test.section_settings ?? []}
          />
        )}
      </Main>

      <SectionEditDialog
        section={editingSection}
        testId={testId}
        open={dialogOpen}
        onOpenChange={(o) => {
          setDialogOpen(o)
          if (!o) setTimeout(() => setEditingSection(null), 300)
        }}
      />

      {test && (
        <PublishValidationDialog
          open={publishOpen}
          onOpenChange={setPublishOpen}
          checks={publishChecks}
          loading={writingQsLoading}
          publishing={publishMutation.isPending}
          onConfirm={(force) => publishMutation.mutate(force)}
        />
      )}
    </>
  )
}
