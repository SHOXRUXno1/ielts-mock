import { useCallback, useEffect, useRef, useState } from 'react'
import { BookOpen, ChevronDown, Loader2, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { uploadImage } from '@/lib/api/attempts'
import { apiErrorMessage } from '@/lib/api/error'
import { createQuestionGroup } from '@/lib/api/question-groups'
import { createSection, updateSection } from '@/lib/api/sections'
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
  READING_TYPES,
  type Section,
  type SectionSettings,
} from '../data/schema'
import { QuestionGroupEditor } from './question-group-editor'
import { SectionDurationField } from './section-duration-field'
import { buildLiveSectionGroups } from './section-groups-live'
import { SectionLivePreview } from './section-live-preview'
import { SectionSplitLayout } from './section-split-layout'
import { EmptyState } from './ui/empty-state'
import { StatusChip } from './ui/status-chip'
import { StepShell } from './ui/step-shell'

type Props = {
  testId: string
  sections: Section[]
  sectionSettings: SectionSettings[]
  onRefresh: () => void
}

export function StepReading({
  testId,
  sections,
  sectionSettings,
  onRefresh,
}: Props) {
  const readingSections = sections
    .filter((s) => s.type === 'reading')
    .sort((a, b) => a.order - b.order)

  const [activeTab, setActiveTab] = useState(readingSections[0]?.id ?? '')
  const [addingPassage, setAddingPassage] = useState(false)

  // If the active tab points at a deleted/stale section, jump to the first live one.
  useEffect(() => {
    if (readingSections.length === 0) {
      if (activeTab) setActiveTab('')
      return
    }
    if (!readingSections.some((s) => s.id === activeTab)) {
      setActiveTab(readingSections[0].id)
    }
  }, [readingSections, activeTab])

  const handleAddPassage = useCallback(async () => {
    setAddingPassage(true)
    try {
      const section = await createSection(testId, { type: 'reading' })
      onRefresh()
      setActiveTab(section.id)
      toast.success('Reading passage added')
    } catch (err) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? 'Failed to add passage'
      toast.error(detail)
    } finally {
      setAddingPassage(false)
    }
  }, [testId, onRefresh])

  const addButton = readingSections.length < 3 ? (
    <Button size='sm' variant='outline' onClick={handleAddPassage} disabled={addingPassage}>
      {addingPassage ? (
        <Loader2 className='mr-1 size-3.5 animate-spin' />
      ) : (
        <Plus className='mr-1 size-3.5' />
      )}
      Add Passage
    </Button>
  ) : undefined

  return (
    <StepShell
      title='Reading'
      description='IELTS Academic Reading has 3 passages with 13-14 questions each (40 total).'
      counter={<StatusChip current={readingSections.length} target={3} />}
      action={addButton}
    >
      <SectionDurationField
        testId={testId}
        sectionType='reading'
        settings={sectionSettings}
        onSaved={onRefresh}
      />

      {readingSections.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          headline='No reading passages yet'
          description='Add the first passage to start building questions.'
          action={
            <Button size='sm' onClick={handleAddPassage} disabled={addingPassage}>
              {addingPassage ? <Loader2 className='mr-1 size-3.5 animate-spin' /> : <Plus className='mr-1 size-3.5' />}
              Add Passage
            </Button>
          }
        />
      ) : (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            {readingSections.map((s, i) => (
              <TabsTrigger key={s.id} value={s.id}>
                Passage {i + 1}
              </TabsTrigger>
            ))}
          </TabsList>

          {readingSections.map((section, passageIdx) => {
            const priorPassageSlots = countScoringSlots(
              readingSections
                .slice(0, passageIdx)
                .flatMap((s) =>
                  (s.question_groups ?? []).flatMap((g) => g.questions),
                ),
            )
            return (
            <TabsContent key={section.id} value={section.id} className='mt-4'>
              <PassageEditor
                testId={testId}
                section={section}
                passageNumber={passageIdx + 1}
                numberOffset={priorPassageSlots}
                onRefresh={onRefresh}
              />
            </TabsContent>
            )
          })}
        </Tabs>
      )}
    </StepShell>
  )
}

function PassageEditor({
  testId,
  section,
  passageNumber,
  numberOffset,
  onRefresh,
}: {
  testId: string
  section: Section
  passageNumber: number
  numberOffset: number
  onRefresh: () => void
}) {
  const imageRef = useRef<HTMLInputElement>(null)
  const [savingMeta, setSavingMeta] = useState(false)
  const [uploadingImg, setUploadingImg] = useState(false)
  const [passage, setPassage] = useState(section.passage ?? '')
  const [title, setTitle] = useState(section.title ?? '')
  const [passageSubtitle, setPassageSubtitle] = useState(section.passage_subtitle ?? '')
  const [imageUrl, setImageUrl] = useState('')
  const [addingGroup, setAddingGroup] = useState(false)
  const [passageOpen, setPassageOpen] = useState(true)

  // Sync local state when section prop updates (e.g. after refetch)
  useEffect(() => {
    setPassage(section.passage ?? '')
    setTitle(section.title ?? '')
    setPassageSubtitle(section.passage_subtitle ?? '')
  }, [section.passage, section.title, section.passage_subtitle])
  const [drafts, setDrafts] = useState<Record<string, CompoundGroupDraft>>({})

  const sortedGroups = [...(section.question_groups ?? [])].sort(
    (a, b) => a.order - b.order,
  )
  const liveSectionGroups = buildLiveSectionGroups(sortedGroups, drafts)

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
        passage: passage || null,
        title: title || null,
        passage_subtitle: passageSubtitle || null,
      })
      toast.success('Passage saved')
      onRefresh()
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Failed to save passage'))
    } finally {
      setSavingMeta(false)
    }
  }

  const handleImageUpload = async (file: File) => {
    setUploadingImg(true)
    try {
      const url = await uploadImage(file)
      setImageUrl(url)
      toast.success('Image uploaded')
    } catch {
      toast.error('Failed to upload image')
    } finally {
      setUploadingImg(false)
    }
  }

  const handleAddGroup = async () => {
    setAddingGroup(true)
    try {
      await createQuestionGroup(section.id, {
        question_type: 'true_false_ng',
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
      <h3 className='font-medium text-foreground'>Passage {passageNumber}</h3>

      <Collapsible open={passageOpen} onOpenChange={setPassageOpen}>
        <div className='rounded-md border border-border'>
          <CollapsibleTrigger asChild>
            <button
              type='button'
              className='flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-foreground hover:bg-muted/50'
            >
              <span>
                Passage text
                {passage.trim() ? (
                  <span className='ml-2 text-xs font-normal text-success-foreground'>
                    set
                  </span>
                ) : (
                  <span className='ml-2 text-xs font-normal text-warning-foreground'>
                    empty
                  </span>
                )}
              </span>
              <ChevronDown
                className={cn(
                  'size-4 text-muted-foreground transition-transform',
                  passageOpen && 'rotate-180',
                )}
              />
            </button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className='space-y-3 border-t border-border p-4'>
              <div className='space-y-1.5'>
                <Label className='text-sm font-medium'>
                  Passage Title (optional)
                </Label>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder='e.g. The History of Urban Planning'
                />
              </div>
              <div className='space-y-1.5'>
                <Label className='text-sm font-medium'>
                  Passage Subtitle (optional)
                </Label>
                <Textarea
                  rows={2}
                  value={passageSubtitle}
                  onChange={(e) => setPassageSubtitle(e.target.value)}
                  placeholder='e.g. In Paris, urban farmers are trying a soil-free approach...'
                  className='text-sm'
                />
              </div>
              <Textarea
                rows={12}
                value={passage}
                onChange={(e) => setPassage(e.target.value)}
                placeholder='Paste or type the passage here. Paragraphs can be labelled A, B, C...'
                className='font-serif text-sm leading-relaxed'
              />
              <p className='mt-1 text-[11px] text-muted-foreground'>
                Formatting: <em>*italic text*</em>, <strong>**bold text**</strong>
              </p>
              <div className='flex items-center gap-2'>
                <input
                  ref={imageRef}
                  type='file'
                  accept='image/*'
                  className='hidden'
                  onChange={(e) => {
                    const f = e.target.files?.[0]
                    if (f) void handleImageUpload(f)
                  }}
                />
                <Button
                  type='button'
                  variant='outline'
                  size='sm'
                  disabled={uploadingImg}
                  onClick={() => imageRef.current?.click()}
                >
                  {uploadingImg ? (
                    <Loader2 className='mr-1 size-3.5 animate-spin' />
                  ) : null}
                  {imageUrl ? 'Replace Image' : 'Upload Image (optional)'}
                </Button>
                {imageUrl && (
                  <span className='text-xs text-success-foreground'>
                    Image attached
                  </span>
                )}
              </div>
              <div className='flex items-center gap-2'>
                <Button
                  variant='outline'
                  size='sm'
                  onClick={() => void handleSaveMeta()}
                  disabled={savingMeta}
                >
                  {savingMeta && (
                    <Loader2 className='mr-1 size-3.5 animate-spin' />
                  )}
                  Save passage
                </Button>
              </div>
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
              allowedTypes={READING_TYPES}
              sectionType='reading'
              onRefresh={onRefresh}
              onDraftChange={(d) => handleDraftChange(group.id, d)}
              numberOffset={numberOffset}
              sectionGroups={liveSectionGroups}
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
      sectionType='reading'
      editor={editor}
      preview={
        <SectionLivePreview
          section={section}
          drafts={drafts}
          numberOffset={numberOffset}
        />
      }
    />
  )
}
