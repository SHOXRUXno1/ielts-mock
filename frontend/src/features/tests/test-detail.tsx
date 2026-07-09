import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getRouteApi, Link } from '@tanstack/react-router'
import {
  ArrowLeft,
  BookOpen,
  ChevronDown,
  ChevronRight,
  Clock,
  ExternalLink,
  Headphones,
  LayoutGrid,
  Mic,
  Pencil,
  PenLine,
  Play,
  HelpCircle,
} from 'lucide-react'
import { fetchTest } from '@/lib/api/tests'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { QuestionList } from './components/question-list'
import { SectionEditDialog } from './components/section-edit-dialog'
import { type Section, type SectionType } from './data/schema'

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

function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} min`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m ? `${h}h ${m}m` : `${h}h`
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

// ── Summary strip ─────────────────────────────────────────────────────────────

function SummaryStrip({ sections, isPublished }: { sections: Section[]; isPublished: boolean }) {
  const totalQuestions = sections.reduce((s, sec) => s + sec.question_count, 0)
  const totalMinutes = sections.reduce((s, sec) => s + sec.duration_minutes, 0)

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
      color: 'text-blue-600',
      bg: 'bg-blue-50 dark:bg-blue-950/30',
    },
    {
      icon: HelpCircle,
      label: 'Questions',
      value: totalQuestions,
      sub: 'total',
      color: 'text-emerald-600',
      bg: 'bg-emerald-50 dark:bg-emerald-950/30',
    },
    {
      icon: Clock,
      label: 'Duration',
      value: formatDuration(totalMinutes),
      sub: `${totalMinutes} minutes`,
      color: 'text-amber-600',
      bg: 'bg-amber-50 dark:bg-amber-950/30',
    },
    {
      icon: isPublished ? Play : Pencil,
      label: 'Status',
      value: isPublished ? 'Published' : 'Draft',
      sub: isPublished ? 'visible to students' : 'not visible',
      color: isPublished ? 'text-emerald-600' : 'text-slate-500',
      bg: isPublished ? 'bg-emerald-50 dark:bg-emerald-950/30' : 'bg-slate-50 dark:bg-slate-800/30',
    },
  ]

  return (
    <div className='grid grid-cols-2 gap-3 sm:grid-cols-4'>
      {cards.map(({ icon: Icon, label, value, sub, color, bg }) => (
        <div
          key={label}
          className='flex items-center gap-3 rounded-xl border bg-card px-4 py-3'
        >
          <div className={`shrink-0 rounded-lg p-2 ${bg}`}>
            <Icon className={`size-4 ${color}`} />
          </div>
          <div className='min-w-0'>
            <p className='text-lg font-bold leading-tight tabular-nums truncate'>{value}</p>
            <p className='text-xs text-muted-foreground'>{label}</p>
            <p className='text-xs text-muted-foreground/60 truncate'>{sub}</p>
          </div>
        </div>
      ))}
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
          {section.duration_minutes} min
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
          <td colSpan={6} className='bg-muted/20 px-5 py-4'>
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
  expandedId,
  onToggle,
  onEdit,
  testId,
}: {
  type: SectionType
  sections: Section[]
  expandedId: string | null
  onToggle: (id: string) => void
  onEdit: (s: Section) => void
  testId: string
}) {
  const meta = TYPE_META[type]
  const Icon = meta.icon
  const totalQ = sections.reduce((s, sec) => s + sec.question_count, 0)
  const totalMin = sections.reduce((s, sec) => s + sec.duration_minutes, 0)

  const sorted = [...sections].sort((a, b) => a.order - b.order)

  return (
    <div>
      {/* Group header */}
      <div className='mb-2 flex items-center gap-3'>
        <div className={`rounded-lg p-1.5 ${meta.bg}`}>
          <Icon className={`size-4 ${meta.color}`} />
        </div>
        <div>
          <span className='font-semibold text-sm'>{meta.label}</span>
          <span className='ml-2 text-xs text-muted-foreground'>
            {sections.length} {sections.length === 1 ? 'section' : 'sections'} · {totalQ} questions · {formatDuration(totalMin)}
          </span>
        </div>
      </div>

      {/* Rows table */}
      <div className='rounded-xl border bg-card overflow-hidden'>
        <table className='w-full'>
          <thead>
            <tr className='border-b bg-muted/30'>
              <th className='py-2 pl-5 pr-3 w-8' />
              <th className='py-2 px-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide'>
                Section
              </th>
              <th className='py-2 px-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide'>
                Duration
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

// ── Main component ────────────────────────────────────────────────────────────

export function TestDetail() {
  const { testId } = route.useParams()
  const [editingSection, setEditingSection] = useState<Section | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const { data: test, isLoading } = useQuery({
    queryKey: ['tests', testId],
    queryFn: () => fetchTest(testId),
  })

  function toggleExpanded(id: string) {
    setExpandedId((prev) => (prev === id ? null : id))
  }

  function openEdit(section: Section) {
    setEditingSection(section)
    setDialogOpen(true)
  }

  // Group sections by type, preserving TYPE_ORDER
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
        {/* Back link */}
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
                <Button asChild>
                  <Link
                    to='/take-test/$bookSlug/$testSlug'
                    params={{
                      bookSlug: test.book_slug,
                      testSlug: `test-${test.test_number}`,
                    }}
                  >
                    <Play className='size-4' />
                    Preview Test
                  </Link>
                </Button>
              </div>
            </div>
          ) : (
            <p className='text-muted-foreground'>Test not found.</p>
          )}
        </div>

        {/* Summary strip */}
        {test && (
          <SummaryStrip sections={test.sections} isPublished={test.is_published} />
        )}

        {/* Sections grouped by type */}
        {test && groupedSections && (
          <div className='space-y-6'>
            <h3 className='text-lg font-semibold'>Sections</h3>
            {TYPE_ORDER.filter((t) => groupedSections[t].length > 0).map((type) => (
              <TypeGroup
                key={type}
                type={type}
                sections={groupedSections[type]}
                expandedId={expandedId}
                onToggle={toggleExpanded}
                onEdit={openEdit}
                testId={testId}
              />
            ))}
          </div>
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
    </>
  )
}
