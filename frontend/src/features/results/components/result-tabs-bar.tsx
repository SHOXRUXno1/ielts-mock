import { LayoutGrid } from 'lucide-react'
import { TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { AttemptDetailRead, EvaluationJobRead } from '@/lib/api/attempts'
import { cn } from '@/lib/utils'
import { formatBand } from '../lib/band'
import { SKILL_META, type SkillKey } from '../lib/skill'
import { isSectionNotAttempted } from '../lib/status'
import { RESULT_TABS } from '../lib/tabs'
import { jobPhase } from '../evaluation-progress'

type ResultTabsBarProps = {
  attempt: AttemptDetailRead
  role?: string | null
}

const SKILL_BAND: Record<SkillKey, keyof AttemptDetailRead> = {
  listening: 'listening_band',
  reading: 'reading_band',
  writing: 'writing_band',
  speaking: 'speaking_band',
}

function jobsFor(attempt: AttemptDetailRead, skill: SkillKey): EvaluationJobRead[] {
  if (skill === 'listening' || skill === 'reading') return []
  return attempt.evaluation_jobs.filter((j) => j.section_type === skill)
}

function TabMeta({
  attempt,
  skill,
}: {
  attempt: AttemptDetailRead
  skill: SkillKey
}) {
  const band = attempt[SKILL_BAND[skill]] as number | null
  const phase = jobPhase(jobsFor(attempt, skill))
  const scoring = phase === 'queued' || phase === 'scoring'
  const empty = isSectionNotAttempted(band, attempt.status) || (band == null && !scoring)

  if (scoring) {
    return (
      <span
        className='size-1.5 animate-pulse rounded-full bg-warning-foreground'
        aria-label={`${SKILL_META[skill].label} scoring`}
      />
    )
  }
  if (empty) {
    return (
      <span
        className='size-1.5 rounded-full bg-muted-foreground/50'
        aria-label={`${SKILL_META[skill].label} not attempted`}
      />
    )
  }
  return (
    <span className='text-[11px] font-medium tabular-nums text-muted-foreground'>
      {formatBand(band)}
    </span>
  )
}

export function ResultTabsBar({ attempt, role }: ResultTabsBarProps) {
  const stickyTop = role === 'student' ? 'top-14 lg:top-16' : 'top-16'

  return (
    <div
      className={cn(
        'sticky z-20 -mx-4 bg-background/80 px-4 py-2 backdrop-blur-lg',
        stickyTop,
      )}
    >
      <TabsList className='no-scrollbar h-auto w-full justify-start overflow-x-auto rounded-xl bg-muted/50 p-1'>
        {RESULT_TABS.map((value) => {
          const skill = value as SkillKey
          const isOverview = value === 'overview'
          const meta = isOverview ? null : SKILL_META[skill]
          const Icon = isOverview ? LayoutGrid : meta!.icon
          return (
            <TabsTrigger
              key={value}
              value={value}
              className='gap-2 rounded-lg px-3 capitalize'
            >
              <Icon className='hidden size-3.5 sm:block' />
              {value}
              {!isOverview && <TabMeta attempt={attempt} skill={skill} />}
            </TabsTrigger>
          )
        })}
      </TabsList>
    </div>
  )
}
