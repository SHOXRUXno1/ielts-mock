import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ChevronDown, Headphones, Loader2, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { createQuestionGroup } from '@/lib/api/question-groups'
import { createSection, updateSection } from '@/lib/api/sections'
import { apiUploadErrorMessage } from '@/lib/api/error'
import { uploadSectionAudio } from '@/lib/api/tests'
import { Button } from '@/components/ui/button'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import type { CompoundGroupDraft } from '../data/compound'
import {
  countScoringSlots,
  listeningSlotNumbers,
  LISTENING_TYPES,
  type Question,
  type Section,
  type SectionSettings,
} from '../data/schema'
import { QuestionGroupEditor } from './question-group-editor'
import { SectionDurationField } from './section-duration-field'
import { buildLiveSectionGroups } from './section-groups-live'
import { SectionLivePreview } from './section-live-preview'
import { SectionSplitLayout } from './section-split-layout'
import { EmptyState } from './ui/empty-state'
import { Notice } from './ui/notice'
import { StatusChip } from './ui/status-chip'
import { StepShell } from './ui/step-shell'

type Props = {
  testId: string
  sections: Section[]
  sectionSettings: SectionSettings[]
  onRefresh: () => void
}

export function StepListening({
  testId,
  sections,
  sectionSettings,
  onRefresh,
}: Props) {
  const listeningSections = sections
    .filter((s) => s.type === 'listening')
    .sort((a, b) => a.order - b.order)

  const [activeTab, setActiveTab] = useState(listeningSections[0]?.id ?? '')
  const [partDirty, setPartDirty] = useState<Record<string, boolean>>({})

  const handleTabChange = useCallback(
    (nextTab: string) => {
      if (partDirty[activeTab]) {
        const ok = window.confirm(
          'You have unsaved changes in this Part. Switch anyway? Unsaved edits will be lost.',
        )
        if (!ok) return
      }
      setActiveTab(nextTab)
    },
    [activeTab, partDirty],
  )

  const handlePartDirtyChange = useCallback(
    (sectionId: string) => (dirty: boolean) => {
      setPartDirty((prev) => {
        if (prev[sectionId] === dirty) return prev
        return { ...prev, [sectionId]: dirty }
      })
    },
    [],
  )

  const [addingPart, setAddingPart] = useState(false)

  const handleAddPart = useCallback(async () => {
    setAddingPart(true)
    try {
      const section = await createSection(testId, { type: 'listening' })
      onRefresh()
      setActiveTab(section.id)
      toast.success('Listening part added')
    } catch (err) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? 'Failed to add listening part'
      toast.error(detail)
    } finally {
      setAddingPart(false)
    }
  }, [testId, onRefresh])

  const addButton = listeningSections.length < 4 ? (
    <Button size='sm' variant='outline' onClick={handleAddPart} disabled={addingPart}>
      {addingPart ? (
        <Loader2 className='mr-1 size-3.5 animate-spin' />
      ) : (
        <Plus className='mr-1 size-3.5' />
      )}
      Add Part
    </Button>
  ) : undefined

  return (
    <StepShell
      title='Listening'
      description='IELTS Listening has 4 parts with 10 questions each (40 total).'
      counter={<StatusChip current={listeningSections.length} target={4} />}
      action={addButton}
    >
      <SectionDurationField
        testId={testId}
        sectionType='listening'
        settings={sectionSettings}
        onSaved={onRefresh}
      />

      {listeningSections.length === 0 ? (
        <EmptyState
          icon={Headphones}
          headline='No listening parts yet'
          description='Add the first listening part to start building questions.'
          action={
            <Button size='sm' onClick={handleAddPart} disabled={addingPart}>
              {addingPart ? <Loader2 className='mr-1 size-3.5 animate-spin' /> : <Plus className='mr-1 size-3.5' />}
              Add Part
            </Button>
          }
        />
      ) : (
        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList>
          {listeningSections.map((s, i) => {
              const fromGroups = (s.question_groups ?? []).flatMap((g) => g.questions)
              const qCount =
                fromGroups.length > 0
                  ? countScoringSlots(fromGroups)
                  : (s.question_count ?? 0)
              return (
                <TabsTrigger key={s.id} value={s.id} className='gap-1.5'>
                  Part {i + 1}
                  {partDirty[s.id] && (
                    <span className='size-1.5 rounded-full bg-warning' title='Unsaved changes' />
                  )}
                  <StatusChip current={qCount} target={10} />
                </TabsTrigger>
              )
            })}
          </TabsList>

          {listeningSections.map((section, partIdx) => (
            <TabsContent key={section.id} value={section.id} className='mt-4'>
              <PartEditor
                testId={testId}
                section={section}
                partNumber={partIdx + 1}
                onRefresh={onRefresh}
                onDirtyChange={handlePartDirtyChange(section.id)}
              />
            </TabsContent>
          ))}
        </Tabs>
      )}
    </StepShell>
  )
}

function PartEditor({
  testId,
  section,
  partNumber,
  onRefresh,
  onDirtyChange,
}: {
  testId: string
  section: Section
  partNumber: number
  onRefresh: () => void
  onDirtyChange?: (dirty: boolean) => void
}) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [savingMeta, setSavingMeta] = useState(false)
  const [addingGroup, setAddingGroup] = useState(false)
  const [drafts, setDrafts] = useState<Record<string, CompoundGroupDraft>>({})
  const [dirtyGroups, setDirtyGroups] = useState<Record<string, boolean>>({})

  // Audio/audioscript: use server value as source of truth, local override only while editing
  const [localAudioUrl, setLocalAudioUrl] = useState<string | null>(null)
  const [localAudioscript, setLocalAudioscript] = useState<string | null>(null)

  const audioUrl = localAudioUrl ?? section.audio_url ?? ''
  const audioscript = localAudioscript ?? section.audioscript ?? ''
  const [audioOpen, setAudioOpen] = useState(!section.audio_url)

  // Reset local overrides when server data updates (after save/refresh)
  const prevAudioRef = useRef(section.audio_url)
  const prevScriptRef = useRef(section.audioscript)
  if (prevAudioRef.current !== section.audio_url) {
    prevAudioRef.current = section.audio_url
    setLocalAudioUrl(null)
    if (section.audio_url) setAudioOpen(false)
  }
  if (prevScriptRef.current !== section.audioscript) {
    prevScriptRef.current = section.audioscript
    setLocalAudioscript(null)
  }
  const hasDirtyGroups = useMemo(
    () => Object.values(dirtyGroups).some(Boolean),
    [dirtyGroups],
  )

  const onDirtyChangeRef = useRef(onDirtyChange)

  useEffect(() => {
    onDirtyChangeRef.current = onDirtyChange
  }, [onDirtyChange])

  useEffect(() => {
    onDirtyChangeRef.current?.(hasDirtyGroups)
  }, [hasDirtyGroups])

  const handleGroupDirtyChange = useCallback(
    (groupId: string, dirty: boolean) => {
      setDirtyGroups((prev) => {
        if (prev[groupId] === dirty) return prev
        return { ...prev, [groupId]: dirty }
      })
    },
    [],
  )

  const sortedGroups = [...(section.question_groups ?? [])].sort(
    (a, b) => a.order - b.order,
  )
  const liveSectionGroups = buildLiveSectionGroups(sortedGroups, drafts)
  const allPartQuestions = liveSectionGroups.flatMap((g) =>
    g.questions.map((q) => ({
      id: q.id,
      section_id: section.id,
      question_group_id: g.id,
      order: q.order,
      question_type: (q.question_type ?? g.question_type ?? 'mcq') as Question['question_type'],
      content: q.content ?? {},
      answer_key: q.answer_key ?? null,
      task_number: null,
      min_words: null,
      image_url: null,
      essay_type: null,
      created_at: '',
      updated_at: '',
    })),
  )
  const partSlotCount = countScoringSlots(allPartQuestions)
  const displayPartCount =
    allPartQuestions.length > 0
      ? partSlotCount
      : (section.question_count ?? 0)
  const slotRanges = listeningSlotNumbers(section.order, allPartQuestions)

  const handleDraftChange = useCallback(
    (groupId: string, draft: CompoundGroupDraft | null) => {
      setDrafts((prev) => {
        if (!draft) {
          if (!(groupId in prev)) return prev
          const next = { ...prev }
          delete next[groupId]
          return next
        }
        const existing = prev[groupId]
        if (existing && JSON.stringify(existing) === JSON.stringify(draft)) {
          return prev
        }
        return { ...prev, [groupId]: draft }
      })
    },
    [],
  )

  const handleSaveMeta = async () => {
    setSavingMeta(true)
    try {
      await updateSection(section.id, {
        audio_url: audioUrl || null,
        audioscript: audioscript || null,
      })
      toast.success('Saved')
      setLocalAudioUrl(null)
      setLocalAudioscript(null)
      if (audioUrl) setAudioOpen(false)
      onRefresh()
    } catch {
      toast.error('Failed to save section')
    } finally {
      setSavingMeta(false)
    }
  }

  const handleAudioUpload = async (file: File) => {
    setUploading(true)
    try {
      const { url } = await uploadSectionAudio(testId, section.id, file)
      setLocalAudioUrl(url)
      toast.success('Audio uploaded')
      setAudioOpen(false)
      try {
        await onRefresh()
      } catch {
        /* File is already saved — a refresh miss must not look like a failed upload. */
      }
    } catch (err) {
      toast.error(apiUploadErrorMessage(err, 'Failed to upload audio'))
    } finally {
      setUploading(false)
    }
  }

  const handleAddGroup = async () => {
    setAddingGroup(true)
    try {
      await createQuestionGroup(section.id, {
        question_type: 'gap_fill',
        instruction: '',
      })
      toast.success('Group added')
      onRefresh()
    } catch {
      toast.error('Failed to add group')
    } finally {
      setAddingGroup(false)
    }
  }

  const editor = (
    <div className='space-y-5'>
      <h3 className='font-medium text-foreground'>Part {partNumber}</h3>

      {displayPartCount !== 10 && (
        <Notice variant='warning'>
          Part must have exactly 10 questions. Current:{' '}
          <span className='font-semibold tabular-nums'>{displayPartCount}</span>
          {' — '}add gaps to reach 10.
        </Notice>
      )}

      <Collapsible open={audioOpen} onOpenChange={setAudioOpen}>
        <div className='rounded-md border border-border'>
          <CollapsibleTrigger asChild>
            <button
              type='button'
              className='flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-foreground hover:bg-muted/50'
            >
              <span>
                Audio
                {audioUrl ? (
                  <span className='ml-2 text-xs font-normal text-success-foreground'>
                    uploaded
                  </span>
                ) : (
                  <span className='ml-2 text-xs font-normal text-warning-foreground'>
                    required
                  </span>
                )}
              </span>
              <ChevronDown
                className={cn(
                  'size-4 text-muted-foreground transition-transform',
                  audioOpen && 'rotate-180',
                )}
              />
            </button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className='space-y-3 border-t border-border p-4'>
              <div className='flex items-center gap-2'>
                <Input
                  value={audioUrl}
                  onChange={(e) => setLocalAudioUrl(e.target.value)}
                  placeholder='/media/audio/part1.mp3 or https://...'
                />
                <input
                  ref={fileRef}
                  type='file'
                  accept='audio/*'
                  className='hidden'
                  onChange={(e) => {
                    const f = e.target.files?.[0]
                    if (f) void handleAudioUpload(f)
                    e.target.value = ''
                  }}
                />
                <Button
                  type='button'
                  variant='outline'
                  size='sm'
                  disabled={uploading}
                  onClick={() => fileRef.current?.click()}
                >
                  {uploading ? (
                    <Loader2 className='size-4 animate-spin' />
                  ) : (
                    'Upload'
                  )}
                </Button>
              </div>
              <div className='space-y-1.5'>
                <Label className='text-xs text-muted-foreground'>
                  Audioscript (optional)
                </Label>
                <Textarea
                  rows={4}
                  value={audioscript}
                  onChange={(e) => setLocalAudioscript(e.target.value)}
                  placeholder='Transcript of the audio recording...'
                />
              </div>
              <Button
                variant='outline'
                size='sm'
                onClick={() => void handleSaveMeta()}
                disabled={savingMeta}
              >
                {savingMeta && (
                  <Loader2 className='mr-1 size-3.5 animate-spin' />
                )}
                Save section info
              </Button>
            </div>
          </CollapsibleContent>
        </div>
      </Collapsible>

      <div className='space-y-3'>
        <Label className='text-sm font-medium'>
          Question Groups ({sortedGroups.length})
        </Label>

        <div className='space-y-4'>
          {sortedGroups.map((group, idx) => (
            <QuestionGroupEditor
              key={group.id}
              group={group}
              groupNumber={idx + 1}
              allowedTypes={LISTENING_TYPES}
              sectionType='listening'
              onRefresh={onRefresh}
              onDraftChange={(d) => handleDraftChange(group.id, d)}
              onDirtyChange={handleGroupDirtyChange}
              numberOffset={(partNumber - 1) * 10}
              sectionGroups={liveSectionGroups}
              slotRanges={slotRanges}
            />
          ))}
        </div>

        <Button
          variant='outline'
          onClick={() => void handleAddGroup()}
          disabled={addingGroup}
        >
          {addingGroup ? (
            <Loader2 className='mr-1 size-4 animate-spin' />
          ) : (
            <Plus className='mr-1 size-4' />
          )}
          Add Question Group
        </Button>
      </div>
    </div>
  )

  return (
    <SectionSplitLayout
      testId={testId}
      sectionType='listening'
      editor={editor}
      preview={
        <SectionLivePreview
          section={section}
          drafts={drafts}
          numberOffset={(partNumber - 1) * 10}
        />
      }
    />
  )
}
