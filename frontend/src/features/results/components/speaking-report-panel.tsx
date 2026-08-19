import type { ReactNode } from 'react'
import { Mic } from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import type {
  AttemptDetailRead,
  EvaluationJobRead,
  SpeakingSessionSummary,
} from '@/lib/api/attempts'
import { cn } from '@/lib/utils'
import { EvaluationProgressCard, jobPhase } from '../evaluation-progress'
import { ENTER } from '../lib/motion'
import { CriteriaGrid, FeedbackList } from '../writing-feedback-panel'
import { AdminBandOverride } from './admin-band-override'
import { ResultEmptyState } from './result-empty-state'
import { SkillReportHeader } from './skill-report-header'
import { Panel, PanelHeader, PanelTitle } from '@/components/report'

type SpeakingReportPanelProps = {
  attempt: AttemptDetailRead
  attemptId: string
  jobs: EvaluationJobRead[]
  isAdmin: boolean
  onOverride: () => void
  finalizeAction?: ReactNode
}

export function SpeakingReportPanel({
  attempt,
  attemptId,
  jobs,
  isAdmin,
  onOverride,
  finalizeAction,
}: SpeakingReportPanelProps) {
  const session: SpeakingSessionSummary | null | undefined = attempt.speaking_session
  const hasBand = attempt.speaking_band != null && attempt.speaking_band > 0
  const job = jobs.find((j) => j.status === 'done') ?? jobs[0]
  const scoreJson =
    (job?.result as Record<string, unknown> | null) ?? session?.score_json ?? null
  const speakingPhase = jobPhase(jobs)
  const turns = session?.history_json ?? []

  if (
    speakingPhase === 'queued' ||
    speakingPhase === 'scoring' ||
    speakingPhase === 'failed'
  ) {
    return <EvaluationProgressCard jobs={jobs} section='speaking' />
  }

  if (hasBand || scoreJson) {
    return (
      <div className='space-y-4'>
        <SkillReportHeader
          skill='speaking'
          band={attempt.speaking_band ?? session?.overall_band}
          action={
            isAdmin && job ? (
              <AdminBandOverride job={job} onOverride={onOverride} />
            ) : undefined
          }
        />
        <div className='grid gap-4 lg:grid-cols-[minmax(0,1fr)_16rem]'>
          <Panel className={ENTER} padding='sm'>
            <div className='space-y-5'>
              {Array.isArray(scoreJson?.strengths) && (
                <FeedbackList
                  title='Strengths'
                  items={scoreJson.strengths as string[]}
                />
              )}
              {Array.isArray(scoreJson?.improvements) && (
                <FeedbackList
                  title='Areas for Improvement'
                  items={scoreJson.improvements as string[]}
                />
              )}
              {typeof scoreJson?.transcript === 'string' && scoreJson.transcript && (
                <div>
                  <p className='mb-2 text-sm font-medium'>Transcript</p>
                  <ScrollArea className='h-56 rounded-lg border bg-surface-sunken'>
                    <p className='whitespace-pre-wrap p-3 text-sm leading-relaxed'>
                      {scoreJson.transcript}
                    </p>
                  </ScrollArea>
                </div>
              )}
              {turns.length > 0 && (
                <div>
                  <PanelHeader className='mb-2 items-baseline'>
                    <PanelTitle className='text-sm'>Conversation</PanelTitle>
                    <p className='text-[11px] tabular-nums text-muted-foreground'>
                      {turns.length} {turns.length === 1 ? 'turn' : 'turns'}
                    </p>
                  </PanelHeader>
                  <ScrollArea className='h-80 rounded-lg border bg-surface-sunken p-3'>
                    <div className='space-y-3'>
                      {turns.map((turn, i) => {
                        const isExaminer = turn.role === 'examiner'
                        return (
                          <div
                            key={i}
                            className={cn(
                              'flex items-end gap-2',
                              isExaminer ? 'justify-start' : 'flex-row-reverse',
                            )}
                          >
                            <Avatar className='size-7'>
                              <AvatarFallback
                                className={cn(
                                  'text-[10px] font-semibold',
                                  isExaminer
                                    ? 'bg-muted text-muted-foreground'
                                    : 'bg-primary text-primary-foreground',
                                )}
                              >
                                {isExaminer ? 'EX' : 'YOU'}
                              </AvatarFallback>
                            </Avatar>
                            <div
                              className={cn(
                                'max-w-[85%] rounded-2xl px-3 py-2 text-sm leading-relaxed',
                                isExaminer
                                  ? 'rounded-bl-md bg-muted text-foreground'
                                  : 'rounded-br-md bg-primary text-primary-foreground',
                              )}
                            >
                              <span className='mb-0.5 block text-[10px] font-medium tracking-wide uppercase opacity-70'>
                                {turn.role}
                              </span>
                              {turn.text}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </ScrollArea>
                </div>
              )}
            </div>
          </Panel>
          {scoreJson && (
            <aside className='lg:sticky lg:top-32 lg:self-start'>
              <CriteriaGrid
                data={scoreJson}
                sectionType='speaking'
                variant='rail'
              />
            </aside>
          )}
        </div>
      </div>
    )
  }

  if (session && session.status === 'in_progress') {
    return (
      <ResultEmptyState
        icon={Mic}
        title='Speaking test in progress'
        description={
          isAdmin
            ? 'The student has an active AI examiner session.'
            : 'Resume your AI examiner session to finish and receive a band score.'
        }
        action={
          isAdmin ? (
            <Button asChild>
              <Link to='/speaking-examiner' search={{ attemptId }}>
                Resume Session
              </Link>
            </Button>
          ) : undefined
        }
      />
    )
  }

  return (
    <ResultEmptyState
      icon={Mic}
      title='Speaking test not started'
      description={
        isAdmin
          ? 'The speaking section has not been taken yet.'
          : 'The speaking section is not available in this view.'
      }
      action={
        isAdmin ? (
          <div className='flex flex-wrap justify-center gap-2'>
            <Button asChild>
              <Link to='/speaking-examiner' search={{ attemptId }}>
                Continue to Speaking
              </Link>
            </Button>
            {finalizeAction}
          </div>
        ) : undefined
      }
    />
  )
}
