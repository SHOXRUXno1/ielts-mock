import type { AttemptDetailRead } from '@/lib/api/attempts'
import { AccuracyByPart } from './accuracy-by-part'
import { InsightsPanel } from './insights-panel'
import { SkillMatrix } from './skill-matrix'
import { SkillRadar } from './skill-radar'

type OverviewPanelProps = {
  attempt: AttemptDetailRead
}

export function OverviewPanel({ attempt }: OverviewPanelProps) {
  return (
    <div className='space-y-6'>
      <div className='grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]'>
        <SkillRadar attempt={attempt} />
        <SkillMatrix attempt={attempt} />
      </div>
      <div className='grid gap-6 lg:grid-cols-2'>
        <InsightsPanel attempt={attempt} />
        <AccuracyByPart attempt={attempt} />
      </div>
    </div>
  )
}
