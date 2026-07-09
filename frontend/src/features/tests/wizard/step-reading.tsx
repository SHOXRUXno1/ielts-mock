import { useRef, useState } from 'react'
import { Loader2, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { uploadImage } from '@/lib/api/attempts'
import { createQuestionGroup } from '@/lib/api/question-groups'
import { updateSection } from '@/lib/api/sections'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import type { QuestionType, Section } from '../data/schema'
import { MigrationBanner } from './migration-banner'
import { QuestionGroupEditor } from './question-group-editor'

const READING_TYPES: QuestionType[] = [
  'mcq', 'gap_fill', 'matching', 'true_false_ng', 'multi_select',
  'matching_headings', 'matching_information', 'matching_features',
  'yes_no_ng', 'sentence_completion', 'short_answer',
]

type Props = {
  testId: string
  sections: Section[]
  onRefresh: () => void
}

export function StepReading({ testId, sections, onRefresh }: Props) {
  const readingSections = sections
    .filter((s) => s.type === 'reading')
    .sort((a, b) => a.order - b.order)

  const [activeTab, setActiveTab] = useState(readingSections[0]?.id ?? '')

  const needsMigration = readingSections.length !== 3

  return (
    <div className='space-y-4'>
      {needsMigration && (
        <MigrationBanner
          testId={testId}
          message={
            readingSections.length < 3
              ? `This test has ${readingSections.length} reading passage(s). IELTS standard requires exactly 3.`
              : `This test has ${readingSections.length} reading passages. IELTS standard requires exactly 3.`
          }
          onRefresh={onRefresh}
        />
      )}

      {readingSections.length === 0 ? (
        <div className='py-8 text-center text-sm text-slate-500'>
          No reading passages found. Click "Migrate to IELTS standard" above to create them.
        </div>
      ) : (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            {readingSections.map((s, i) => (
              <TabsTrigger key={s.id} value={s.id}>
                Passage {i + 1}
              </TabsTrigger>
            ))}
          </TabsList>

          {readingSections.map((section, passageIdx) => (
            <TabsContent key={section.id} value={section.id} className='space-y-5'>
              <PassageEditor
                section={section}
                passageNumber={passageIdx + 1}
                onRefresh={onRefresh}
              />
            </TabsContent>
          ))}
        </Tabs>
      )}
    </div>
  )
}

function PassageEditor({
  section,
  passageNumber,
  onRefresh,
}: {
  section: Section
  passageNumber: number
  onRefresh: () => void
}) {
  const imageRef = useRef<HTMLInputElement>(null)
  const [savingMeta, setSavingMeta] = useState(false)
  const [uploadingImg, setUploadingImg] = useState(false)
  const [passage, setPassage] = useState(section.passage ?? '')
  const [title, setTitle] = useState(section.title ?? '')
  const [duration, setDuration] = useState(section.duration_minutes || 20)
  const [imageUrl, setImageUrl] = useState('')
  const [addingGroup, setAddingGroup] = useState(false)

  const sortedGroups = [...(section.question_groups ?? [])].sort((a, b) => a.order - b.order)

  const handleSaveMeta = async () => {
    setSavingMeta(true)
    try {
      await updateSection(section.id, {
        passage: passage || null,
        title: title || null,
        duration_minutes: duration,
      })
      toast.success('Passage saved')
      onRefresh()
    } catch {
      toast.error('Failed to save passage')
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

  return (
    <div className='space-y-5'>
      <h3 className='font-medium text-slate-900'>Passage {passageNumber}</h3>

      {/* Passage meta */}
      <div className='space-y-3 rounded-md border border-slate-200 p-4'>
        <div className='space-y-1.5'>
          <Label className='text-sm font-medium'>Passage Title (optional)</Label>
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder='e.g. The History of Urban Planning'
          />
        </div>

        <Label className='text-sm font-medium'>Passage Text</Label>
        <Textarea
          rows={14}
          value={passage}
          onChange={(e) => setPassage(e.target.value)}
          placeholder='Paste or type the passage here. Paragraphs can be labelled A, B, C...'
          className='font-serif text-sm leading-relaxed'
        />
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
            {uploadingImg ? <Loader2 className='mr-1 size-3.5 animate-spin' /> : null}
            {imageUrl ? 'Replace Image' : 'Upload Image (optional)'}
          </Button>
          {imageUrl && (
            <span className='text-xs text-emerald-600'>Image attached ✓</span>
          )}
        </div>
        <div className='flex items-center gap-2'>
          <Label className='text-xs text-slate-500'>Duration (min)</Label>
          <Input
            type='number'
            min={5}
            max={60}
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            className='h-8 w-20 text-sm'
          />
          <Button variant='outline' size='sm' onClick={() => void handleSaveMeta()} disabled={savingMeta}>
            {savingMeta && <Loader2 className='mr-1 size-3.5 animate-spin' />}
            Save passage
          </Button>
        </div>
      </div>

      {/* Question Groups */}
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
              onRefresh={onRefresh}
            />
          ))}
        </div>

        <Button variant='outline' onClick={() => void handleAddGroup()} disabled={addingGroup}>
          {addingGroup ? <Loader2 className='mr-1 size-4 animate-spin' /> : <Plus className='mr-1 size-4' />}
          Add Question Group
        </Button>
      </div>
    </div>
  )
}
