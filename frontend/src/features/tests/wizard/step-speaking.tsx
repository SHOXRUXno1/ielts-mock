import { useState } from 'react'
import { Loader2, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import {
  createQuestion,
  deleteQuestion,
  updateQuestion,
} from '@/lib/api/questions'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import type { Question, Section } from '../data/schema'
import { MigrationBanner } from './migration-banner'

type Props = {
  testId: string
  sections: Section[]
  questionsMap: Record<string, Question[]>
  onRefresh: () => void
}

export function StepSpeaking({ testId, sections, questionsMap, onRefresh }: Props) {
  const speakingSections = sections
    .filter((s) => s.type === 'speaking')
    .sort((a, b) => a.order - b.order)

  const [activeTab, setActiveTab] = useState(speakingSections[0]?.id ?? '')

  const needsMigration = speakingSections.length !== 3

  const partLabels = ['Part 1 — Introduction', 'Part 2 — Cue Card', 'Part 3 — Discussion']

  return (
    <div className='space-y-4'>
      {needsMigration && (
        <MigrationBanner
          testId={testId}
          message={
            speakingSections.length < 3
              ? `This test has ${speakingSections.length} speaking part(s). IELTS standard requires exactly 3.`
              : `This test has ${speakingSections.length} speaking parts. IELTS standard requires exactly 3.`
          }
          onRefresh={onRefresh}
        />
      )}

      {speakingSections.length === 0 ? (
        <div className='py-8 text-center text-sm text-slate-500'>
          No speaking sections found. Click "Migrate to IELTS standard" above to create them.
        </div>
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
    </div>
  )
}

// ── Helpers to read canonical or legacy content ───────────────────────────────

/** Extract prompts array from a Part 1/3 question (canonical or legacy). */
function getPromptList(questions: Question[]): string[] {
  if (questions.length === 0) return []
  const first = questions[0]
  const c = first.content

  // Canonical: { part, questions: [str] }
  if (Array.isArray(c.questions)) return c.questions as string[]

  // Legacy: multiple questions each with { prompt }
  return questions.map((q) => String(q.content.prompt ?? '')).filter(Boolean)
}

// ── Part 1 & Part 3: manages a single question with { part, questions: [] } ──

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

  const canonicalQuestion = questions.find((q) => Array.isArray(q.content.questions))
  const legacyQuestions = questions.filter((q) => !Array.isArray(q.content.questions))

  const handleSave = async (updatedPrompts: string[]) => {
    setSaving(true)
    try {
      const content = { part: partNumber, questions: updatedPrompts }

      if (canonicalQuestion) {
        await updateQuestion(section.id, canonicalQuestion.id, { content })
      } else {
        // Create new canonical question (and old legacy ones remain for backward compat — migration will clean them up)
        await createQuestion(section.id, {
          order: 1,
          question_type: 'speaking_part',
          content,
        })
        // Delete legacy questions now that we have a canonical one
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
      <h3 className='font-medium text-slate-900'>{label}</h3>
      <p className='text-xs text-slate-500'>
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
    <div className='flex items-start gap-2 rounded-md border border-slate-200 p-3'>
      <span className='mt-0.5 text-xs font-medium text-slate-400'>{index + 1}.</span>
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
            className='flex-1 cursor-pointer text-sm text-slate-800 hover:text-slate-600'
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

// ── Part 2: Cue card ──────────────────────────────────────────────────────────

function readCueCard(questions: Question[]) {
  if (questions.length === 0) return { topic: '', bullets: '', followUp: '' }
  const c = questions[0].content

  // Canonical: { part: 2, cue_card: { topic, bullets, follow_up } }
  if (c.cue_card && typeof c.cue_card === 'object') {
    const cc = c.cue_card as Record<string, unknown>
    return {
      topic: String(cc.topic ?? ''),
      bullets: Array.isArray(cc.bullets) ? (cc.bullets as string[]).join('\n') : String(cc.bullets ?? ''),
      followUp: String(cc.follow_up ?? ''),
    }
  }

  // Legacy: { topic, bullets }
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
      <h3 className='font-medium text-slate-900'>{label}</h3>
      <p className='text-xs text-slate-500'>
        Enter the cue card topic and the bullet points the candidate should address.
      </p>

      <div className='space-y-3 rounded-md border border-slate-200 p-4'>
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
            Bullet points <span className='font-normal text-slate-400'>(one per line)</span>
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
            Follow-up question <span className='font-normal text-slate-400'>(optional)</span>
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
