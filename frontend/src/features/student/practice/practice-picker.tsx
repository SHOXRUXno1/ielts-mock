import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import { ArrowRight, Clock, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import {
  fetchPracticeUnits,
  startPracticeAttempt,
  type PracticeScope,
  type PracticeSectionUnit,
  type PracticeUnit,
} from '@/lib/api/practice'
import { fetchSlugRedirect } from '@/lib/api/tests'
import { useAuthStore } from '@/stores/auth-store'
import type { SectionType } from '@/features/tests/data/schema'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { cn } from '@/lib/utils'
import { SKILL_ICONS } from './skill-icons'

const TYPE_META: Record<
  SectionType,
  {
    label: string
    icon: string
    accent: string
    accentSoft: string
    ring: string
    chip: string
  }
> = {
  listening: {
    label: 'Listening',
    icon: SKILL_ICONS.listening,
    accent: 'text-sky-700 dark:text-sky-300',
    accentSoft: 'from-sky-50 to-white dark:from-sky-950/50 dark:to-card',
    ring: 'ring-sky-200/80 dark:ring-sky-800/60',
    chip: 'bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300',
  },
  reading: {
    label: 'Reading',
    icon: SKILL_ICONS.reading,
    accent: 'text-emerald-700 dark:text-emerald-300',
    accentSoft: 'from-emerald-50 to-white dark:from-emerald-950/50 dark:to-card',
    ring: 'ring-emerald-200/80 dark:ring-emerald-800/60',
    chip: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
  },
  writing: {
    label: 'Writing',
    icon: SKILL_ICONS.writing,
    accent: 'text-violet-700 dark:text-violet-300',
    accentSoft: 'from-violet-50 to-white dark:from-violet-950/50 dark:to-card',
    ring: 'ring-violet-200/80 dark:ring-violet-800/60',
    chip: 'bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-300',
  },
  speaking: {
    label: 'Speaking',
    icon: SKILL_ICONS.speaking,
    accent: 'text-amber-700 dark:text-amber-300',
    accentSoft: 'from-amber-50 to-white dark:from-amber-950/50 dark:to-card',
    ring: 'ring-amber-200/80 dark:ring-amber-800/60',
    chip: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
  },
}

function formatRelative(iso: string | null | undefined): string {
  if (!iso) return ''
  const then = new Date(iso).getTime()
  if (!Number.isFinite(then)) return ''
  const diffMs = Date.now() - then
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  if (days <= 0) return 'today'
  if (days === 1) return 'yesterday'
  if (days < 7) return `${days}d ago`
  const weeks = Math.floor(days / 7)
  if (weeks < 5) return `${weeks}w ago`
  return `${Math.floor(days / 30)}mo ago`
}

function SkillIcon({
  src,
  label,
  size = 'md',
}: {
  src: string
  label: string
  size?: 'sm' | 'md' | 'lg'
}) {
  const dim =
    size === 'lg' ? 'size-14' : size === 'sm' ? 'size-9' : 'size-11'
  return (
    <img
      src={src}
      alt=''
      aria-hidden
      draggable={false}
      className={cn(
        dim,
        'shrink-0 object-contain drop-shadow-[0_10px_18px_rgba(15,23,42,0.18)] select-none',
      )}
      title={label}
    />
  )
}

type Props = {
  testId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

type StartTarget =
  | { scope: 'part'; unit: PracticeUnit }
  | { scope: 'section'; unit: PracticeSectionUnit }

/**
 * Senior practice picker: 3D skill icons, clear Full-section hero CTA,
 * compact part grid underneath. One job — choose what to practise.
 */
export function PracticePicker({ testId, open, onOpenChange }: Props) {
  const navigate = useNavigate()
  const [pending, setPending] = useState<string | null>(null)
  const signedIn = useAuthStore((s) => Boolean(s.auth.accessToken))

  const unitsQuery = useQuery({
    queryKey: ['practice-units', testId],
    queryFn: () => fetchPracticeUnits(testId),
    enabled: open && signedIn,
  })

  const slugsQuery = useQuery({
    queryKey: ['slug-redirect', testId],
    queryFn: () => fetchSlugRedirect(testId),
    enabled: open && signedIn,
    staleTime: Infinity,
  })

  const startMutation = useMutation({
    mutationFn: async (target: StartTarget) => {
      const attempt = await startPracticeAttempt(testId, {
        section_type: target.unit.section_type,
        scope: target.scope,
        part_number:
          target.scope === 'part' ? target.unit.part_number : undefined,
      })
      const slugs = slugsQuery.data ?? (await fetchSlugRedirect(testId))
      return { attempt, slugs, target }
    },
    onSuccess: async ({ attempt, slugs, target }) => {
      onOpenChange(false)
      const part =
        target.scope === 'part' ? String(target.unit.part_number) : '1'
      await navigate({
        to: '/practice/$bookSlug/$testSlug/$section/$part',
        params: {
          bookSlug: slugs.book_slug,
          testSlug: `test-${slugs.test_number}`,
          section: target.unit.section_type,
          part,
        },
        search: {
          attempt: attempt.id,
          scope: target.scope as PracticeScope,
        },
      })
    },
    onError: (err: unknown) => {
      setPending(null)
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? 'Failed to start practice'
      toast.error(detail)
    },
  })

  const units = unitsQuery.data?.units ?? []
  const sections = unitsQuery.data?.sections ?? []
  const grouped = units.reduce<Record<SectionType, PracticeUnit[]>>(
    (acc, unit) => {
      const key = unit.section_type
      if (!acc[key]) acc[key] = []
      acc[key].push(unit)
      return acc
    },
    { listening: [], reading: [], writing: [], speaking: [] },
  )
  const sectionByType = Object.fromEntries(
    sections.map((s) => [s.section_type, s]),
  ) as Partial<Record<SectionType, PracticeSectionUnit>>

  const orderedTypes = (
    ['listening', 'reading', 'writing', 'speaking'] as SectionType[]
  ).filter((t) => grouped[t].length > 0 || sectionByType[t])

  const busy = startMutation.isPending && pending != null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className='max-w-[44rem] gap-0 overflow-hidden p-0 sm:rounded-2xl'>
        <div className='border-b border-border/70 bg-gradient-to-b from-muted/40 to-background px-6 pb-4 pt-6'>
          <DialogHeader className='gap-1.5 text-left'>
            <DialogTitle className='text-xl font-semibold tracking-tight'>
              Practice
            </DialogTitle>
            <DialogDescription className='text-[13.5px] leading-relaxed'>
              Full section for exam pace, or a single part for focused drills.
              Practice stays separate from your mock results.
            </DialogDescription>
          </DialogHeader>
        </div>

        {unitsQuery.isLoading ? (
          <div className='flex items-center justify-center py-16 text-sm text-muted-foreground'>
            <Loader2 className='mr-2 size-4 animate-spin' /> Loading…
          </div>
        ) : orderedTypes.length === 0 ? (
          <div className='px-6 py-14 text-center text-sm text-muted-foreground'>
            This test does not have any practice-ready content yet.
          </div>
        ) : (
          <div className='max-h-[min(70vh,640px)] space-y-6 overflow-y-auto px-6 py-5'>
            {orderedTypes.map((type) => {
              const meta = TYPE_META[type]
              const full = sectionByType[type]
              const parts = grouped[type].sort(
                (a, b) => a.part_number - b.part_number,
              )
              return (
                <section key={type} className='space-y-3'>
                  <div className='flex items-center gap-2.5'>
                    <SkillIcon src={meta.icon} label={meta.label} size='sm' />
                    <div>
                      <h3 className='text-[15px] font-semibold leading-none'>
                        {meta.label}
                      </h3>
                      <p className='mt-1 text-[11px] text-muted-foreground'>
                        {full
                          ? `${full.part_count} parts available`
                          : `${parts.length} parts available`}
                      </p>
                    </div>
                  </div>

                  {full && (
                    <FullSectionCard
                      unit={full}
                      meta={meta}
                      pending={pending === `section-${type}`}
                      disabled={busy}
                      onStart={() => {
                        setPending(`section-${type}`)
                        startMutation.mutate({ scope: 'section', unit: full })
                      }}
                    />
                  )}

                  {parts.length > 0 && (
                    <div>
                      <p className='mb-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground/80'>
                        Or practise one part
                      </p>
                      <div className='grid grid-cols-2 gap-2 sm:grid-cols-4'>
                        {parts.map((unit) => (
                          <PartCard
                            key={`${unit.section_type}-${unit.part_number}`}
                            unit={unit}
                            meta={meta}
                            pending={
                              pending ===
                              `${unit.section_type}-${unit.part_number}`
                            }
                            disabled={busy}
                            onStart={() => {
                              setPending(
                                `${unit.section_type}-${unit.part_number}`,
                              )
                              startMutation.mutate({ scope: 'part', unit })
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </section>
              )
            })}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

function FullSectionCard({
  unit,
  meta,
  pending,
  disabled,
  onStart,
}: {
  unit: PracticeSectionUnit
  meta: (typeof TYPE_META)[SectionType]
  pending: boolean
  disabled: boolean
  onStart: () => void
}) {
  const durationLabel =
    unit.duration_minutes != null
      ? `${unit.duration_minutes} min`
      : 'AI-paced'
  const clickable = unit.is_enabled && !disabled
  const last = unit.last_attempt
  const lastLabel =
    last == null
      ? null
      : last.band != null
        ? `Band ${last.band.toFixed(1)}`
        : last.correct != null && last.total
          ? `${last.correct}/${last.total}`
          : 'Completed'

  return (
    <button
      type='button'
      disabled={!clickable}
      onClick={onStart}
      className={cn(
        'group relative flex w-full items-center gap-4 overflow-hidden rounded-2xl border bg-gradient-to-r p-3.5 text-left ring-1 transition-all',
        meta.accentSoft,
        meta.ring,
        clickable
          ? 'hover:-translate-y-0.5 hover:shadow-md'
          : 'cursor-not-allowed opacity-50',
        pending && 'ring-2 ring-primary/50',
      )}
    >
      <div className='flex size-16 shrink-0 items-center justify-center rounded-2xl bg-white/80 shadow-sm ring-1 ring-black/5 dark:bg-background/60'>
        <SkillIcon src={meta.icon} label={unit.label} size='lg' />
      </div>

      <div className='min-w-0 flex-1'>
        <div className='flex flex-wrap items-center gap-2'>
          <span className='text-[15px] font-semibold tracking-tight'>
            {unit.label}
          </span>
          <span
            className={cn(
              'rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide',
              meta.chip,
            )}
          >
            Exam pace
          </span>
          {pending && (
            <Loader2 className='size-3.5 animate-spin text-primary' />
          )}
        </div>

        <div className='mt-1.5 flex flex-wrap items-center gap-x-2.5 gap-y-1 text-[12px] text-muted-foreground'>
          <span className='inline-flex items-center gap-1'>
            <Clock className='size-3 opacity-70' />
            {durationLabel}
          </span>
          {unit.question_count > 0 && (
            <span>{unit.question_count} questions</span>
          )}
          {unit.part_count > 0 && <span>{unit.part_count} parts</span>}
        </div>

        {lastLabel && (
          <p className={cn('mt-1.5 text-[12px] font-medium', meta.accent)}>
            Last {lastLabel}
            {last?.finished_at && (
              <span className='font-normal text-muted-foreground'>
                {' '}
                · {formatRelative(last.finished_at)}
              </span>
            )}
          </p>
        )}
      </div>

      <span
        className={cn(
          'hidden shrink-0 items-center gap-1 rounded-xl bg-foreground px-3 py-2 text-xs font-semibold text-background transition-transform sm:inline-flex',
          clickable && 'group-hover:translate-x-0.5',
        )}
      >
        Start
        <ArrowRight className='size-3.5' />
      </span>
    </button>
  )
}

function PartCard({
  unit,
  meta,
  pending,
  disabled,
  onStart,
}: {
  unit: PracticeUnit
  meta: (typeof TYPE_META)[SectionType]
  pending: boolean
  disabled: boolean
  onStart: () => void
}) {
  const durationLabel =
    unit.duration_minutes != null
      ? `${unit.duration_minutes} min`
      : 'AI-paced'
  const clickable = unit.is_enabled && !disabled
  const last = unit.last_attempt
  const lastScore =
    last && last.correct != null && last.total
      ? `${last.correct}/${last.total}`
      : null

  return (
    <button
      type='button'
      disabled={!clickable}
      onClick={onStart}
      className={cn(
        'flex flex-col rounded-xl border bg-card p-3 text-left transition-all',
        clickable
          ? 'hover:-translate-y-0.5 hover:border-foreground/15 hover:shadow-sm'
          : 'cursor-not-allowed opacity-50',
        pending && 'ring-2 ring-primary/40',
      )}
    >
      <div className='flex items-start justify-between gap-2'>
        <span className='text-[13px] font-semibold'>{unit.label}</span>
        {pending ? (
          <Loader2 className='size-3.5 animate-spin text-primary' />
        ) : (
          <ArrowRight className='size-3.5 text-muted-foreground/50' />
        )}
      </div>

      <div className='mt-1.5 flex items-center gap-1.5 text-[11px] text-muted-foreground'>
        <Clock className='size-3 opacity-70' />
        <span>{durationLabel}</span>
        {unit.question_count > 0 && (
          <>
            <span className='text-muted-foreground/40'>·</span>
            <span>{unit.question_count} q</span>
          </>
        )}
      </div>

      {lastScore ? (
        <div className={cn('mt-2 text-[11px] font-medium', meta.accent)}>
          {lastScore}
          <span className='font-normal text-muted-foreground'>
            {' '}
            · {formatRelative(last?.finished_at ?? undefined)}
          </span>
        </div>
      ) : !unit.is_enabled ? (
        <span className='mt-2 text-[10px] text-muted-foreground'>
          Not available
        </span>
      ) : (
        <span className='mt-2 text-[11px] text-muted-foreground/70'>
          Not tried yet
        </span>
      )}
    </button>
  )
}
