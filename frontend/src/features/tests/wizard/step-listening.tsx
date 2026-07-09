import { useRef, useState } from 'react'
import { Loader2, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { createQuestionGroup } from '@/lib/api/question-groups'
import { updateSection } from '@/lib/api/sections'
import { uploadSectionAudio } from '@/lib/api/tests'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import type { QuestionType, Section } from '../data/schema'
import { MigrationBanner } from './migration-banner'
import { QuestionGroupEditor } from './question-group-editor'

const LISTENING_TYPES: QuestionType[] = [
  'mcq', 'gap_fill', 'matching', 'map_labeling', 'true_false_ng', 'multi_select',
  'matching_information', 'matching_features',
  'sentence_completion', 'short_answer',
]

type Props = {
  testId: string
  sections: Section[]
  onRefresh: () => void
}

export function StepListening({ testId, sections, onRefresh }: Props) {
  const listeningSections = sections
    .filter((s) => s.type === 'listening')
    .sort((a, b) => a.order - b.order)

  const [activeTab, setActiveTab] = useState(listeningSections[0]?.id ?? '')

  const needsMigration = listeningSections.length !== 4

  return (
    <div className='space-y-4'>
      {needsMigration && (
        <MigrationBanner
          testId={testId}
          message={
            listeningSections.length < 4
              ? `This test has ${listeningSections.length} listening part(s). IELTS standard requires exactly 4.`
              : `This test has ${listeningSections.length} listening parts. IELTS standard requires exactly 4.`
          }
          onRefresh={onRefresh}
        />
      )}

      {listeningSections.length === 0 ? (
        <div className='py-8 text-center text-sm text-slate-500'>
          No listening sections found. Click "Migrate to IELTS standard" above to create them.
        </div>
      ) : (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            {listeningSections.map((s, i) => (
              <TabsTrigger key={s.id} value={s.id}>
                Part {i + 1}
              </TabsTrigger>
            ))}
          </TabsList>

          {listeningSections.map((section, partIdx) => (
            <TabsContent key={section.id} value={section.id} className='space-y-5'>
              <PartEditor
                testId={testId}
                section={section}
                partNumber={partIdx + 1}
                onRefresh={onRefresh}
              />
            </TabsContent>
          ))}
        </Tabs>
      )}
    </div>
  )
}

function PartEditor({
  testId,
  section,
  partNumber,
  onRefresh,
}: {
  testId: string
  section: Section
  partNumber: number
  onRefresh: () => void
}) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [savingMeta, setSavingMeta] = useState(false)
  const [audioUrl, setAudioUrl] = useState(section.audio_url ?? '')
  const [audioscript, setAudioscript] = useState(section.audioscript ?? '')
  const [addingGroup, setAddingGroup] = useState(false)

  const sortedGroups = [...(section.question_groups ?? [])].sort((a, b) => a.order - b.order)

  const handleSaveMeta = async () => {
    setSavingMeta(true)
    try {
      await updateSection(section.id, {
        audio_url: audioUrl || null,
        audioscript: audioscript || null,
        duration_minutes: section.duration_minutes,
      })
      toast.success('Saved')
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
      setAudioUrl(url)
      await updateSection(section.id, { audio_url: url })
      toast.success('Audio uploaded')
      onRefresh()
    } catch {
      toast.error('Failed to upload audio')
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

  return (
    <div className='space-y-5'>
      <h3 className='font-medium text-slate-900'>Part {partNumber}</h3>

      {/* Audio */}
      <div className='space-y-3 rounded-md border border-slate-200 p-4'>
        <Label className='text-sm font-medium'>Audio</Label>
        <div className='flex items-center gap-2'>
          <Input
            value={audioUrl}
            onChange={(e) => setAudioUrl(e.target.value)}
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
            {uploading ? <Loader2 className='size-4 animate-spin' /> : 'Upload'}
          </Button>
        </div>
        <div className='space-y-1.5'>
          <Label className='text-xs text-slate-500'>Audioscript (optional)</Label>
          <Textarea
            rows={4}
            value={audioscript}
            onChange={(e) => setAudioscript(e.target.value)}
            placeholder='Transcript of the audio recording...'
          />
        </div>
        <Button variant='outline' size='sm' onClick={() => void handleSaveMeta()} disabled={savingMeta}>
          {savingMeta && <Loader2 className='mr-1 size-3.5 animate-spin' />}
          Save section info
        </Button>
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
              allowedTypes={LISTENING_TYPES}
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
