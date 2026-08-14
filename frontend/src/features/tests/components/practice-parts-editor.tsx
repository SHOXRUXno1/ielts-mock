import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  BookOpen,
  Clock,
  Headphones,
  Info,
  Loader2,
  Mic,
  PenLine,
  Timer,
} from 'lucide-react'
import { toast } from 'sonner'
import {
  fetchAdminPracticeParts,
  updateAdminPracticePart,
  type PracticePartSetting,
} from '@/lib/api/practice'
import type { SectionSettings, SectionType } from '@/features/tests/data/schema'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'

type Props = {
  testId: string
  sectionSettings: SectionSettings[]
}

const TYPE_META: Record<
  SectionType,
  { label: string; icon: typeof Headphones; color: string; bg: string }
> = {
  listening: { label: 'Listening', icon: Headphones, color: 'text-blue-600', bg: 'bg-blue-500/10' },
  reading: { label: 'Reading', icon: BookOpen, color: 'text-emerald-600', bg: 'bg-emerald-500/10' },
  writing: { label: 'Writing', icon: PenLine, color: 'text-violet-600', bg: 'bg-violet-500/10' },
  speaking: { label: 'Speaking', icon: Mic, color: 'text-amber-600', bg: 'bg-amber-500/10' },
}

/**
 * Per-part practice duration editor + read-only Full-section row.
 *
 * Full-section duration comes from TestSectionSettings (edited elsewhere).
 */
export function PracticePartsEditor({ testId, sectionSettings }: Props) {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['admin-practice-parts', testId],
    queryFn: () => fetchAdminPracticeParts(testId),
  })

  if (isLoading) {
    return (
      <div className='rounded-xl border bg-card p-6 text-sm text-muted-foreground'>
        <Loader2 className='inline size-4 animate-spin' /> Loading practice settings…
      </div>
    )
  }

  const rows = data ?? []
  if (rows.length === 0) {
    return (
      <div className='rounded-xl border bg-card p-6 text-sm text-muted-foreground'>
        Add some sections and questions first — practice units are generated from them.
      </div>
    )
  }

  const grouped = rows.reduce<Record<SectionType, PracticePartSetting[]>>(
    (acc, row) => {
      const key = row.section_type
      if (!acc[key]) acc[key] = []
      acc[key].push(row)
      return acc
    },
    { listening: [], reading: [], writing: [], speaking: [] },
  )

  const durationByType = Object.fromEntries(
    sectionSettings.map((s) => [s.section_type, s.duration_minutes]),
  ) as Partial<Record<SectionType, number | null>>

  return (
    <div className='space-y-5'>
      <div className='flex items-start justify-between gap-3'>
        <div>
          <h3 className='text-lg font-semibold'>Practice settings</h3>
          <p className='mt-1 text-sm text-muted-foreground'>
            Students can practise a full section or any single part. Full-section
            duration follows the section timer above; per-part timers can be
            overridden here.
          </p>
        </div>
      </div>

      {(['listening', 'reading', 'writing', 'speaking'] as SectionType[])
        .filter((t) => grouped[t].length > 0)
        .map((type) => {
          const meta = TYPE_META[type]
          const Icon = meta.icon
          const fullMins = durationByType[type]
          return (
            <div key={type}>
              <div className='mb-2 flex items-center gap-2.5'>
                <div className={`rounded-lg p-1.5 ${meta.bg}`}>
                  <Icon className={`size-4 ${meta.color}`} />
                </div>
                <span className='text-sm font-semibold'>{meta.label}</span>
              </div>
              <div className='space-y-2 rounded-xl border bg-card p-4'>
                <FullSectionRow
                  type={type}
                  durationMinutes={fullMins ?? null}
                />
                {grouped[type]
                  .sort((a, b) => a.part_number - b.part_number)
                  .map((row) => (
                    <PartRow
                      key={`${row.section_type}-${row.part_number}`}
                      testId={testId}
                      row={row}
                      onSaved={() =>
                        queryClient.invalidateQueries({
                          queryKey: ['admin-practice-parts', testId],
                        })
                      }
                    />
                  ))}
              </div>
            </div>
          )
        })}
    </div>
  )
}

function FullSectionRow({
  type,
  durationMinutes,
}: {
  type: SectionType
  durationMinutes: number | null
}) {
  const label =
    type === 'speaking'
      ? 'AI-paced (safety cap)'
      : durationMinutes != null
        ? `${durationMinutes} min`
        : 'Untimed'
  return (
    <div className='flex flex-wrap items-center gap-3 border-b border-border/40 py-2'>
      <div className='min-w-[110px] text-sm font-semibold'>Full section</div>
      <Badge variant='secondary' className='gap-1 text-[10px]'>
        <Timer className='size-3' />
        {label}
      </Badge>
      <span className='inline-flex items-center gap-1 text-xs text-muted-foreground'>
        <Info className='size-3' />
        Uses the section duration above
      </span>
    </div>
  )
}

function PartRow({
  testId,
  row,
  onSaved,
}: {
  testId: string
  row: PracticePartSetting
  onSaved: () => void
}) {
  const [minutes, setMinutes] = useState<string>(
    row.duration_minutes != null ? String(row.duration_minutes) : '',
  )
  const [enabled, setEnabled] = useState<boolean>(row.is_enabled)
  const parsed = minutes.trim() === '' ? null : Number(minutes)
  const invalid =
    parsed !== null && (!Number.isFinite(parsed) || parsed < 1 || parsed > 120)
  const dirty =
    (row.duration_minutes ?? null) !== parsed || row.is_enabled !== enabled

  const mutation = useMutation({
    mutationFn: (payload: {
      duration_minutes: number | null
      is_enabled: boolean
    }) =>
      updateAdminPracticePart(
        testId,
        row.section_type,
        row.part_number,
        payload,
      ),
    onSuccess: () => {
      toast.success('Practice settings saved')
      onSaved()
    },
    onError: (err: unknown) => {
      toast.error(
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? 'Failed to save',
      )
    },
  })

  const partLabel =
    row.section_type === 'reading'
      ? `Passage ${row.part_number}`
      : row.section_type === 'writing'
        ? `Task ${row.part_number}`
        : `Part ${row.part_number}`

  const defaultLabel =
    row.section_type === 'speaking'
      ? 'AI-paced'
      : row.effective_duration_minutes != null
        ? `Default ${row.effective_duration_minutes} min`
        : 'Untimed'

  return (
    <div className='flex flex-wrap items-center gap-3 border-b border-border/40 py-2 last:border-0'>
      <div className='min-w-[110px] text-sm font-medium'>{partLabel}</div>
      <div className='flex items-center gap-2'>
        <Label htmlFor={`d-${row.section_type}-${row.part_number}`} className='sr-only'>
          Duration in minutes
        </Label>
        <div className='relative'>
          <Clock className='absolute left-2 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground' />
          <Input
            id={`d-${row.section_type}-${row.part_number}`}
            type='number'
            min={1}
            max={120}
            placeholder={
              row.section_type === 'speaking'
                ? 'AI'
                : row.effective_duration_minutes != null
                  ? String(row.effective_duration_minutes)
                  : ''
            }
            value={minutes}
            onChange={(e) => setMinutes(e.target.value)}
            className='h-8 w-24 pl-7 text-sm'
            aria-invalid={invalid || undefined}
          />
        </div>
        <span className='text-xs text-muted-foreground'>min</span>
      </div>
      <Badge variant='secondary' className='gap-1 text-[10px]'>
        <Timer className='size-3' />
        {defaultLabel}
      </Badge>
      <div className='ms-auto flex items-center gap-2'>
        <div className='flex items-center gap-2'>
          <Label
            htmlFor={`e-${row.section_type}-${row.part_number}`}
            className='text-xs text-muted-foreground'
          >
            Enabled
          </Label>
          <Switch
            id={`e-${row.section_type}-${row.part_number}`}
            checked={enabled}
            onCheckedChange={setEnabled}
          />
        </div>
        <Button
          size='sm'
          variant='outline'
          disabled={!dirty || invalid || mutation.isPending}
          onClick={() =>
            mutation.mutate({
              duration_minutes: parsed,
              is_enabled: enabled,
            })
          }
        >
          {mutation.isPending && <Loader2 className='mr-1 size-3 animate-spin' />}
          Save
        </Button>
      </div>
    </div>
  )
}
