import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Info, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { updateSectionDuration } from '@/lib/api/section-settings'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Switch } from '@/components/ui/switch'
import {
  DURATION_RULES,
  durationByType,
  durationRangeError,
  modeByType,
} from '../data/duration-rules'
import type { DurationMode, SectionSettings, SectionType } from '../data/schema'

type Props = {
  testId: string
  sectionType: SectionType
  settings: SectionSettings[] | undefined
  onSaved?: () => void
}

const SECTION_LABELS: Record<SectionType, string> = {
  listening: 'Listening',
  reading: 'Reading',
  writing: 'Writing',
  speaking: 'Speaking',
}

/** Map legacy audio_length → custom so the radio group stays valid. */
function normalizeMode(mode: DurationMode | string): DurationMode {
  return mode === 'standard' ? 'standard' : 'custom'
}

/**
 * Section-level timing editor. One duration per section type — parts inside a
 * section share it, and the student decides how to split their time.
 */
export function SectionDurationField({
  testId,
  sectionType,
  settings,
  onSaved,
}: Props) {
  const rule = DURATION_RULES[sectionType]
  const saved = durationByType(settings)[sectionType]
  const savedMode = normalizeMode(modeByType(settings)[sectionType])
  const queryClient = useQueryClient()

  const [mode, setMode] = useState<DurationMode>(
    sectionType === 'speaking' && saved == null ? 'standard' : savedMode,
  )
  const [capped, setCapped] = useState(saved != null)
  const [value, setValue] = useState(saved == null ? '' : String(saved))

  // Reset the draft whenever the server value changes (save, refetch, tab switch).
  const [lastSaved, setLastSaved] = useState(saved)
  const [lastMode, setLastMode] = useState(savedMode)
  if (lastSaved !== saved || lastMode !== savedMode) {
    setLastSaved(saved)
    setLastMode(savedMode)
    setMode(
      sectionType === 'speaking' && saved == null ? 'standard' : savedMode,
    )
    setCapped(saved != null)
    setValue(saved == null ? '' : String(saved))
  }

  const parsed = value.trim() === '' ? null : Number(value)
  const isSpeaking = sectionType === 'speaking'
  const untimed = isSpeaking && !capped
  const draft = untimed ? null : parsed
  const error =
    mode === 'custom' && draft == null && !isSpeaking
      ? `${SECTION_LABELS[sectionType]} duration is required.`
      : mode === 'custom' && !untimed
        ? durationRangeError(sectionType, draft)
        : null

  const dirty =
    mode !== savedMode ||
    (mode === 'custom' && draft !== saved) ||
    (isSpeaking && (untimed ? saved != null : draft !== saved))

  const mutation = useMutation({
    mutationFn: (payload: {
      duration_mode?: DurationMode
      duration_minutes?: number | null
    }) => updateSectionDuration(testId, sectionType, payload),
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: ['tests', testId] })
      if (result.warning) {
        toast.warning(result.warning, {
          action:
            rule.recommended != null
              ? {
                  label: `Use ${rule.recommended} min`,
                  onClick: () =>
                    mutation.mutate({
                      duration_mode: 'standard',
                    }),
                }
              : undefined,
        })
      } else {
        toast.success('Section duration updated')
      }
      onSaved?.()
    },
    onError: (err: unknown) => {
      toast.error(extractDetail(err) ?? 'Failed to update duration')
    },
  })

  const handleSave = () => {
    if (isSpeaking) {
      if (untimed) {
        mutation.mutate({
          duration_mode: 'standard',
          duration_minutes: null,
        })
      } else {
        mutation.mutate({
          duration_mode: 'custom',
          duration_minutes: draft,
        })
      }
      return
    }
    if (mode === 'standard') {
      mutation.mutate({ duration_mode: 'standard' })
      return
    }
    mutation.mutate({
      duration_mode: 'custom',
      duration_minutes: draft,
    })
  }

  const inputDisabled = !isSpeaking && mode !== 'custom'
  const displayValue =
    mode === 'standard' && rule.recommended != null
      ? String(rule.recommended)
      : value

  return (
    <div className='space-y-3 rounded-md border border-border p-4'>
      <div className='flex items-center justify-between'>
        <Label className='text-sm font-medium'>Section Duration</Label>
        <span className='text-xs text-muted-foreground'>
          {SECTION_LABELS[sectionType]}
        </span>
      </div>

      {isSpeaking ? (
        <div className='flex items-center gap-2'>
          <Switch
            id='speaking-cap'
            checked={capped}
            onCheckedChange={(next) => {
              setCapped(next)
              if (!next) {
                setValue('')
                setMode('standard')
              } else {
                if (!value) setValue('20')
                setMode('custom')
              }
            }}
          />
          <Label htmlFor='speaking-cap' className='text-xs text-muted-foreground'>
            Set a hard cap
          </Label>
        </div>
      ) : (
        <RadioGroup
          value={mode}
          onValueChange={(next) => {
            const m = next as DurationMode
            setMode(m)
            if (m === 'standard' && rule.recommended != null) {
              setValue(String(rule.recommended))
            } else if (m === 'custom' && saved != null) {
              setValue(String(saved))
            }
          }}
          className='flex flex-col space-y-1.5'
        >
          <div className='flex items-center gap-2'>
            <RadioGroupItem value='standard' id={`${sectionType}-mode-standard`} />
            <Label
              htmlFor={`${sectionType}-mode-standard`}
              className='text-sm font-normal'
            >
              Standard IELTS
              {rule.recommended != null ? ` (${rule.recommended} min)` : ''}
            </Label>
          </div>
          <div className='flex items-center gap-2'>
            <RadioGroupItem value='custom' id={`${sectionType}-mode-custom`} />
            <Label
              htmlFor={`${sectionType}-mode-custom`}
              className='text-sm font-normal'
            >
              Custom
            </Label>
          </div>
        </RadioGroup>
      )}

      {untimed ? (
        <p className='text-sm text-muted-foreground'>AI-paced (untimed)</p>
      ) : (
        <div className='flex flex-wrap items-center gap-2'>
          <Label className='text-xs text-muted-foreground'>Duration (min)</Label>
          <Input
            type='number'
            min={rule.min ?? undefined}
            max={rule.max ?? undefined}
            value={displayValue}
            onChange={(e) => setValue(e.target.value)}
            disabled={inputDisabled}
            className='h-8 w-24 text-sm'
            aria-label={`${SECTION_LABELS[sectionType]} duration in minutes`}
            aria-invalid={error != null}
          />
          {dirty && !error && (
            <span
              className='size-1.5 rounded-full bg-warning'
              title='Unsaved changes'
            />
          )}
          <Button
            variant='outline'
            size='sm'
            disabled={!dirty || error != null || mutation.isPending}
            onClick={handleSave}
          >
            {mutation.isPending && (
              <Loader2 className='mr-1 size-3.5 animate-spin' />
            )}
            Save section settings
          </Button>
        </div>
      )}

      {untimed && dirty && (
        <Button
          variant='outline'
          size='sm'
          disabled={mutation.isPending}
          onClick={handleSave}
        >
          {mutation.isPending && (
            <Loader2 className='mr-1 size-3.5 animate-spin' />
          )}
          Save section settings
        </Button>
      )}

      {error ? (
        <p className='text-xs text-destructive'>{error}</p>
      ) : !untimed ? (
        <p className='flex items-start gap-1.5 text-[11px] text-muted-foreground'>
          <Info className='mt-px size-3 shrink-0' />
          {mode === 'standard'
            ? 'Standard is recommended for mock exams.'
            : rule.hint}
        </p>
      ) : null}
    </div>
  )
}

function extractDetail(err: unknown): string | null {
  const detail = (
    err as { response?: { data?: { detail?: unknown } } }
  )?.response?.data?.detail
  return typeof detail === 'string' ? detail : null
}
