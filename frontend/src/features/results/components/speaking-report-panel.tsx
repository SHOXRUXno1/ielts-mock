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
import { CriteriaGrid, FeedbackList } from '../writing-feedback-panel'
import { AdminBandOverride } from './admin-band-override'
import { ReportHeader } from './report-header'
import { ResultEmptyState } from './result-empty-state'

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
        <ReportHeader
          skill='speaking'
          band={attempt.speaking_band ?? session?.overall_band}
          action={
            isAdmin && job ? (
              <AdminBandOverride job={job} onOverride={onOverride} />
            ) : undefined
          }
        />
        <div className='grid gap-4 lg:grid-cols-[minmax(0,1fr)_16rem]'>
          <div className='space-y-5 rounded-2xl bg-card p-5 shadow-sm ring-1 ring-border'>
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
                <ScrollArea className='h-56 rounded-lg border bg-muted/30'>
                  <p className='whitespace-pre-wrap p-3 text-sm leading-relaxed'>
                    {scoreJson.transcript}
                  </p>
                </ScrollArea>
              </div>
            )}
            {session?.history_json && session.history_json.length > 0 && (
              <div>
                <p className='mb-2 text-sm font-medium'>Conversation</p>
                <ScrollArea className='h-80 rounded-lg border p-3'>
                  <div className='space-y-3'>
                    {session.history_json.map((turn, i) => {
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
