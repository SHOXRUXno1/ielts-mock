import { LayoutGrid } from 'lucide-react'
import { TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { AttemptDetailRead, EvaluationJobRead } from '@/lib/api/attempts'
import { cn } from '@/lib/utils'
import { jobPhase } from '../evaluation-progress'
import { formatBand } from '../lib/band'
import { SKILL_BAND_FIELD, SKILL_META, type SkillKey } from '../lib/skill'
import { isSectionNotAttempted } from '../lib/status'
import { RESULT_TABS } from '../lib/tabs'

type ResultNavProps = {
  attempt: AttemptDetailRead
  role?: string | null
}

const NAV_STICKY_TOP: Record<string, string> = {
  student: 'top-14 lg:top-16',
  admin: 'top-16',
}

function jobsFor(attempt: AttemptDetailRead, skill: SkillKey): EvaluationJobRead[] {
  if (skill === 'listening' || skill === 'reading') return []
  return attempt.evaluation_jobs.filter((job) => job.section_type === skill)
}

function TabMeta({
  attempt,
  skill,
}: {
  attempt: AttemptDetailRead
  skill: SkillKey
}) {
  const band = attempt[SKILL_BAND_FIELD[skill]]
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
    <span className='font-manrope text-[11px] font-medium tabular-nums text-muted-foreground'>
      {formatBand(band)}
    </span>
  )
}

export function ResultNav({ attempt, role }: ResultNavProps) {
  const stickyTop = NAV_STICKY_TOP[role ?? ''] ?? NAV_STICKY_TOP.admin

  return (
    <div
      className={cn(
        'sticky z-20 -mx-4 border-b border-border bg-background/80 px-4 backdrop-blur-lg',
        stickyTop,
      )}
    >
      <TabsList className='scroll-fade-x no-scrollbar h-auto w-full justify-start gap-1 overflow-x-auto rounded-none bg-transparent p-0'>
        {RESULT_TABS.map((value) => {
          const skill = value as SkillKey
          const isOverview = value === 'overview'
          const meta = isOverview ? null : SKILL_META[skill]
          const Icon = isOverview ? LayoutGrid : meta!.icon
          return (
            <TabsTrigger
              key={value}
              value={value}
              className={cn(
                'relative h-auto flex-none rounded-none border-0 bg-transparent px-3 py-2.5 shadow-none',
                'text-muted-foreground capitalize after:absolute after:inset-x-3 after:bottom-0 after:h-0.5 after:rounded-full after:bg-transparent',
                'hover:text-foreground data-[state=active]:bg-transparent data-[state=active]:text-foreground data-[state=active]:shadow-none data-[state=active]:after:bg-foreground',
                'dark:data-[state=active]:border-transparent dark:data-[state=active]:bg-transparent',
              )}
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
