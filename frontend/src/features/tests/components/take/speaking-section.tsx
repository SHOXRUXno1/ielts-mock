import { useRef, useState, type MutableRefObject } from 'react'
import { CheckCircle2, Mic } from 'lucide-react'
import {
  SpeakingExaminerSession,
  type SpeakingSessionControls,
} from '@/features/speaking-examiner/speaking-examiner-session'
import type { Question } from '../../data/schema'

function extractPrompts(questions: Question[]): string[] {
  const prompts: string[] = []
  for (const q of questions) {
    const c = q.content as Record<string, unknown> | undefined
    if (!c) continue
    if (Array.isArray(c.questions)) {
      for (const p of c.questions) {
        if (typeof p === 'string' && p.trim()) prompts.push(p)
      }
    } else if (typeof c.cue_card === 'object' && c.cue_card !== null) {
      const cc = c.cue_card as Record<string, unknown>
      const topic = cc.topic
      if (typeof topic === 'string' && topic.trim()) prompts.push(topic)
    } else if (typeof c.prompt === 'string' && c.prompt.trim()) {
      prompts.push(c.prompt)
    } else if (typeof c.topic === 'string' && c.topic.trim()) {
      prompts.push(c.topic)
    }
  }
  return prompts
}

type SpeakingSectionProps = {
  attemptId: string | null
  questions: Question[]
  previewMode?: boolean
  onActiveChange?: (active: boolean) => void
  controlsRef?: MutableRefObject<SpeakingSessionControls | null>
  onComplete?: (band: number | null) => void
}

export function SpeakingSection({
  attemptId,
  questions,
  previewMode = false,
  onActiveChange,
  controlsRef,
  onComplete,
}: SpeakingSectionProps) {
  const [done, setDone] = useState(false)
  const internalControlsRef = useRef<SpeakingSessionControls | null>(null)
  const resolvedControlsRef = controlsRef ?? internalControlsRef

  const isPreview = previewMode || !attemptId || attemptId === 'preview'

  const handleComplete = (band: number | null) => {
    setDone(true)
    onComplete?.(band)
  }

  if (isPreview) {
    const prompts = extractPrompts(questions)
    return (
      <div className='flex h-full flex-col items-center justify-center gap-6 overflow-y-auto px-4 py-16'>
        <div className='flex size-20 items-center justify-center rounded-2xl bg-violet-100'>
          <Mic className='size-9 text-violet-600' />
        </div>
        <div className='max-w-md text-center'>
          <h2 className='text-2xl font-bold text-slate-900'>Speaking Section</h2>
          <p className='mt-2 text-slate-500'>
            The Speaking section will be available when the student takes the test.
            It is conducted live with an AI examiner.
          </p>
        </div>
        {prompts.length > 0 && (
          <div className='w-full max-w-lg space-y-2'>
            <h3 className='text-sm font-semibold uppercase tracking-wide text-slate-500'>
              Sample prompts
            </h3>
            <ul className='space-y-1.5'>
              {prompts.map((p, i) => (
                <li
                  key={i}
                  className='rounded-lg border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-700'
                >
                  {p}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    )
  }

  if (done) {
    return (
      <div className='flex h-full flex-col items-center justify-center gap-4 px-4 py-16'>
        <div className='flex size-16 items-center justify-center rounded-2xl bg-emerald-100'>
          <CheckCircle2 className='size-8 text-emerald-600' />
        </div>
        <div className='max-w-md text-center'>
          <h2 className='text-xl font-bold text-slate-900'>Speaking Complete</h2>
          <p className='mt-1 text-sm text-slate-500'>
            Your speaking score has been saved. Continue reviewing other sections or submit your
            test.
          </p>
        </div>
      </div>
    )
  }

  return (
    <SpeakingExaminerSession
      attemptId={attemptId}
      mode='embedded'
      autoStart
      onActiveChange={onActiveChange}
      controlsRef={resolvedControlsRef}
      onComplete={handleComplete}
    />
  )
}
