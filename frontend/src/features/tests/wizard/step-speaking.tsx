import { useCallback, useState } from 'react'
import { Loader2, Mic, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import {
  createQuestion,
  deleteQuestion,
  updateQuestion,
} from '@/lib/api/questions'
import { createSection } from '@/lib/api/sections'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import type { Question, Section, SectionSettings } from '../data/schema'
import { countAuthoredSpeakingParts } from '../lib/speaking-content'
import { SectionDurationField } from './section-duration-field'
import { EmptyState } from './ui/empty-state'
import { StatusChip } from './ui/status-chip'
import { StepShell } from './ui/step-shell'

type Props = {
  testId: string
  sections: Section[]
  sectionSettings: SectionSettings[]
  questionsMap: Record<string, Question[]>
  onRefresh: () => void
}

export function StepSpeaking({
  testId,
  sections,
  sectionSettings,
  questionsMap,
  onRefresh,
}: Props) {
  const speakingSections = sections
    .filter((s) => s.type === 'speaking')
    .sort((a, b) => a.order - b.order)

  const [activeTab, setActiveTab] = useState(speakingSections[0]?.id ?? '')
  const [addingPart, setAddingPart] = useState(false)

  const partLabels = ['Part 1 — Introduction', 'Part 2 — Cue Card', 'Part 3 — Discussion']

  const handleAddPart = useCallback(async () => {
    setAddingPart(true)
    try {
      const section = await createSection(testId, { type: 'speaking' })
      onRefresh()
      setActiveTab(section.id)
      toast.success('Speaking part added')
    } catch (err) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? 'Failed to add speaking part'
      toast.error(detail)
    } finally {
      setAddingPart(false)
    }
  }, [testId, onRefresh])

  const addButton = speakingSections.length < 3 ? (
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
      title='Speaking'
      description='IELTS Speaking has 3 parts. Add Part 1 questions, a Part 2 cue card, and Part 3 discussion prompts.'
      counter={
        <StatusChip
          current={countAuthoredSpeakingParts(speakingSections, questionsMap)}
          target={3}
        />
      }
      action={addButton}
    >
      <SectionDurationField
        testId={testId}
        sectionType='speaking'
        settings={sectionSettings}
        onSaved={onRefresh}
      />

      {speakingSections.length === 0 ? (
        <EmptyState
          icon={Mic}
          headline='No speaking parts yet'
          description='Add the first speaking part to start adding prompts.'
          action={
            <Button size='sm' onClick={handleAddPart} disabled={addingPart}>
              {addingPart ? <Loader2 className='mr-1 size-3.5 animate-spin' /> : <Plus className='mr-1 size-3.5' />}
              Add Part
            </Button>
          }
        />
      ) : (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            {speakingSections.map((s, i) => (
              <TabsTrigger key={s.id} value={s.id}>
                Part {i + 1}
              </TabsTrigger>
            ))}
          </TabsList>

          {speakingSections.map((section, idx) => {
            const questions = questionsMap[section.id] ?? []
            const isCueCard = idx === 1
            const partNumber = idx + 1
            const label = partLabels[idx] ?? `Part ${partNumber}`

            return (
              <TabsContent key={section.id} value={section.id} className='space-y-5'>
                {isCueCard ? (
                  <CueCardEditor
                    section={section}
                    questions={questions}
                    label={label}
                    partNumber={partNumber}
                    onRefresh={onRefresh}
                  />
                ) : (
                  <QuestionListEditor
                    section={section}
                    questions={questions}
                    label={label}
                    partNumber={partNumber}
                    onRefresh={onRefresh}
                  />
                )}
              </TabsContent>
            )
          })}
        </Tabs>
      )}
    </StepShell>
  )
}

function getPromptList(questions: Question[]): string[] {
  if (questions.length === 0) return []
  const first = questions[0]
  const c = first.content ?? {}
  if (Array.isArray(c.questions)) return c.questions as string[]
  return questions.map((q) => String(q.content?.prompt ?? '')).filter(Boolean)
}

function QuestionListEditor({
  section,
  questions,
  label,
  partNumber,
  onRefresh,
}: {
  section: Section
  questions: Question[]
  label: string
  partNumber: number
  onRefresh: () => void
}) {
  const [prompts, setPrompts] = useState<string[]>(() => getPromptList(questions))
  const [newPrompt, setNewPrompt] = useState('')
  const [saving, setSaving] = useState(false)

  const canonicalQuestion = questions.find((q) => Array.isArray(q.content?.questions))
  const legacyQuestions = questions.filter((q) => !Array.isArray(q.content?.questions))

  const handleSave = async (updatedPrompts: string[]) => {
    setSaving(true)
    try {
      const content = { part: partNumber, questions: updatedPrompts }
      if (canonicalQuestion) {
        await updateQuestion(section.id, canonicalQuestion.id, { content })
      } else {
        await createQuestion(section.id, {
          order: 1,
          question_type: 'speaking_part',
          content,
        })
        for (const lq of legacyQuestions) {
          await deleteQuestion(section.id, lq.id)
        }
      }
      toast.success('Saved')
      onRefresh()
    } catch {
      toast.error('Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const addPrompt = async () => {
    const trimmed = newPrompt.trim()
    if (!trimmed) return
    const updated = [...prompts, trimmed]
    setPrompts(updated)
    setNewPrompt('')
    await handleSave(updated)
  }

  const removePrompt = async (index: number) => {
    const updated = prompts.filter((_, i) => i !== index)
    setPrompts(updated)
    await handleSave(updated)
  }

  const updatePrompt = async (index: number, value: string) => {
    const updated = prompts.map((p, i) => (i === index ? value : p))
    setPrompts(updated)
    await handleSave(updated)
  }

  return (
    <div className='space-y-4'>
      <h3 className='font-medium text-foreground'>{label}</h3>
      <p className='text-xs text-muted-foreground'>
        Add speaking prompts for this part. Each prompt is one question the examiner will ask.
      </p>

      <div className='space-y-2'>
        {prompts.map((prompt, i) => (
          <PromptRow
            key={i}
            index={i}
            value={prompt}
            saving={saving}
            onSave={(v) => void updatePrompt(i, v)}
            onDelete={() => void removePrompt(i)}
          />
        ))}
      </div>

      <div className='flex items-center gap-2'>
        <Input
          value={newPrompt}
          onChange={(e) => setNewPrompt(e.target.value)}
          placeholder='e.g. Do you enjoy listening to music?'
          onKeyDown={(e) => { if (e.key === 'Enter') void addPrompt() }}
        />
        <Button
          variant='outline'
          size='sm'
          onClick={() => void addPrompt()}
          disabled={saving || !newPrompt.trim()}
        >
          {saving ? <Loader2 className='size-4 animate-spin' /> : <Plus className='size-4' />}
          Add
        </Button>
      </div>
    </div>
  )
}

function PromptRow({
  index,
  value,
  saving,
  onSave,
  onDelete,
}: {
  index: number
  value: string
  saving: boolean
  onSave: (v: string) => void
  onDelete: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)

  return (
    <div className='flex items-start gap-2 rounded-md border border-border p-3'>
      <span className='mt-0.5 text-xs font-medium text-muted-foreground'>{index + 1}.</span>
      {editing ? (
        <div className='flex flex-1 items-center gap-2'>
          <Input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className='flex-1'
            autoFocus
          />
          <Button
            size='sm'
            onClick={() => { onSave(draft); setEditing(false) }}
            disabled={saving}
          >
            {saving ? <Loader2 className='size-3.5 animate-spin' /> : 'Save'}
          </Button>
          <Button size='sm' variant='ghost' onClick={() => { setDraft(value); setEditing(false) }}>
            Cancel
          </Button>
        </div>
      ) : (
        <div className='flex flex-1 items-center justify-between gap-2'>
          <span
            className='flex-1 cursor-pointer text-sm text-foreground hover:text-muted-foreground'
            onClick={() => setEditing(true)}
          >
            {value}
          </span>
          <div className='flex items-center gap-1'>
            <Button size='sm' variant='ghost' onClick={() => setEditing(true)} className='h-7 px-2 text-xs'>
              Edit
            </Button>
            <Button
              size='sm'
              variant='ghost'
              className='h-7 px-2 text-destructive'
              onClick={onDelete}
              disabled={saving}
            >
              <Trash2 className='size-3.5' />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

function readCueCard(questions: Question[]) {
  if (questions.length === 0) return { topic: '', bullets: '', followUp: '' }
  const c = questions[0].content ?? {}
  if (c.cue_card && typeof c.cue_card === 'object') {
    const cc = c.cue_card as Record<string, unknown>
    return {
      topic: String(cc.topic ?? ''),
      bullets: Array.isArray(cc.bullets) ? (cc.bullets as string[]).join('\n') : String(cc.bullets ?? ''),
      followUp: String(cc.follow_up ?? ''),
    }
  }
  return {
    topic: String(c.topic ?? ''),
    bullets: Array.isArray(c.bullets) ? (c.bullets as string[]).join('\n') : '',
    followUp: '',
  }
}

function CueCardEditor({
  section,
  questions,
  label,
  partNumber,
  onRefresh,
}: {
  section: Section
  questions: Question[]
  label: string
  partNumber: number
  onRefresh: () => void
}) {
  const initial = readCueCard(questions)
  const [topic, setTopic] = useState(initial.topic)
  const [bulletsRaw, setBulletsRaw] = useState(initial.bullets)
  const [followUp, setFollowUp] = useState(initial.followUp)
  const [saving, setSaving] = useState(false)

  const existingQuestion = questions[0]

  const handleSave = async () => {
    setSaving(true)
    try {
      const bullets = bulletsRaw.split('\n').map((b) => b.trim()).filter(Boolean)
      const content = {
        part: partNumber,
        cue_card: {
          topic: topic.trim(),
          bullets,
          follow_up: followUp.trim() || undefined,
        },
      }
      if (existingQuestion) {
        await updateQuestion(section.id, existingQuestion.id, { content })
      } else {
        await createQuestion(section.id, {
          order: 1,
          question_type: 'speaking_part',
          content,
        })
      }
      toast.success('Cue card saved')
      onRefresh()
    } catch {
      toast.error('Failed to save cue card')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className='space-y-4'>
      <h3 className='font-medium text-foreground'>{label}</h3>
      <p className='text-xs text-muted-foreground'>
        Enter the cue card topic and the bullet points the candidate should address.
      </p>

      <div className='space-y-3 rounded-md border border-border p-4'>
        <div className='space-y-1.5'>
          <Label className='text-sm font-medium'>Topic</Label>
          <Input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder='e.g. Describe a memorable journey you have taken.'
          />
        </div>

        <div className='space-y-1.5'>
          <Label className='text-sm font-medium'>
            Bullet points <span className='font-normal text-muted-foreground'>(one per line)</span>
          </Label>
          <Textarea
            rows={5}
            value={bulletsRaw}
            onChange={(e) => setBulletsRaw(e.target.value)}
            placeholder={'Where you went\nWho you went with\nWhat you did\nHow you felt about it'}
          />
        </div>

        <div className='space-y-1.5'>
          <Label className='text-sm font-medium'>
            Follow-up question <span className='font-normal text-muted-foreground'>(optional)</span>
          </Label>
          <Input
            value={followUp}
            onChange={(e) => setFollowUp(e.target.value)}
            placeholder='e.g. And why was this journey so memorable?'
          />
        </div>

        <Button onClick={() => void handleSave()} disabled={saving || !topic.trim()}>
          {saving && <Loader2 className='mr-1 size-4 animate-spin' />}
          Save cue card
        </Button>
      </div>
    </div>
  )
}
