import type { AttemptDetailRead } from '@/lib/api/attempts'
import { OBJECTIVE_QUESTION_TOTAL } from '../lib/answers'
import { BandBreakdown } from './band-breakdown'
import { PerformanceInsights } from './performance-insights'
import { SkillBandCard } from './skill-band-card'

type OverviewPanelProps = {
  attempt: AttemptDetailRead
}

export function OverviewPanel({ attempt }: OverviewPanelProps) {
  const writingJobs = attempt.evaluation_jobs.filter((j) => j.section_type === 'writing')
  const speakingJobs = attempt.evaluation_jobs.filter((j) => j.section_type === 'speaking')

  return (
    <div className='space-y-6'>
      <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
        <SkillBandCard
          skill='listening'
          band={attempt.listening_band}
          raw={attempt.listening_raw}
          total={OBJECTIVE_QUESTION_TOTAL}
          attemptStatus={attempt.status}
          index={0}
        />
        <SkillBandCard
          skill='reading'
          band={attempt.reading_band}
          raw={attempt.reading_raw}
          total={OBJECTIVE_QUESTION_TOTAL}
          attemptStatus={attempt.status}
          index={1}
        />
        <SkillBandCard
          skill='writing'
          band={attempt.writing_band}
          attemptStatus={attempt.status}
          evalJobs={writingJobs}
          index={2}
        />
        <SkillBandCard
          skill='speaking'
          band={attempt.speaking_band}
          attemptStatus={attempt.status}
          evalJobs={speakingJobs}
          index={3}
        />
      </div>
      <div className='grid gap-4 lg:grid-cols-[1.4fr_1fr]'>
        <BandBreakdown attempt={attempt} />
        <PerformanceInsights attempt={attempt} />
      </div>
    </div>
  )
}
