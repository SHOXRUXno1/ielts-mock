import type { ReactNode } from 'react'
import { AudioLines, Lightbulb, MessageSquareText, Mic, Sparkles } from 'lucide-react'
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
import { Panel } from '@/components/report'

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
          variant='feature'
          action={
            isAdmin && job ? (
              <AdminBandOverride job={job} onOverride={onOverride} />
            ) : undefined
          }
        />
        <Panel className={ENTER} padding='md'>
          <div className='space-y-8'>
            {scoreJson && (
              <section>
                <ReportHeading icon={AudioLines} title='Assessment by criterion' description='Your speaking performance across the four IELTS criteria.' />
                <div className='mt-4'><CriteriaGrid data={scoreJson} sectionType='speaking' variant='report' /></div>
              </section>
            )}
            {(Array.isArray(scoreJson?.strengths) || Array.isArray(scoreJson?.improvements)) && (
              <section className='rounded-2xl bg-muted/45 p-5 sm:p-6'>
                <ReportHeading icon={Sparkles} title='Overall review' description='The clearest strengths and the next areas to practise.' />
                <div className='mt-5 grid gap-5 md:grid-cols-2'>
                  {Array.isArray(scoreJson?.strengths) && <FeedbackList title='What went well' items={scoreJson.strengths as string[]} />}
                  {Array.isArray(scoreJson?.improvements) && <FeedbackList title='What to improve next' items={scoreJson.improvements as string[]} />}
                </div>
              </section>
            )}
            {typeof scoreJson?.transcript === 'string' && scoreJson.transcript && (
              <section>
                <ReportHeading icon={MessageSquareText} title='Your transcript' description='A written record of your spoken response.' />
                <ScrollArea className='mt-4 h-64 rounded-xl border bg-surface-sunken'>
                  <p className='whitespace-pre-wrap p-5 text-sm leading-7'>{scoreJson.transcript}</p>
                </ScrollArea>
              </section>
            )}
            {turns.length > 0 && (
              <section>
                <div className='flex items-end justify-between gap-3'>
                  <ReportHeading icon={Mic} title='Conversation with the examiner' />
                  <p className='text-xs tabular-nums text-muted-foreground'>{turns.length} {turns.length === 1 ? 'turn' : 'turns'}</p>
                </div>
                <ScrollArea className='mt-4 h-96 rounded-xl border bg-surface-sunken p-4'>
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
              </section>
            )}
            {!scoreJson && <section className='rounded-2xl bg-muted/45 p-5'><ReportHeading icon={Lightbulb} title='Your speaking feedback will appear here' /></section>}
          </div>
        </Panel>
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

function ReportHeading({ icon: Icon, title, description }: { icon: typeof Mic; title: string; description?: string }) {
  return <div className='flex gap-3'><div className='mt-0.5 rounded-lg bg-muted p-2'><Icon className='size-4 text-muted-foreground' /></div><div><h3 className='font-manrope text-base font-semibold'>{title}</h3>{description && <p className='mt-0.5 text-sm text-muted-foreground'>{description}</p>}</div></div>
}
