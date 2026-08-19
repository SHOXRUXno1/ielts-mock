import { Link } from '@tanstack/react-router'
import { ChevronRight } from 'lucide-react'
import type { AttemptDetailRead, EvaluationJobRead } from '@/lib/api/attempts'
import { cn } from '@/lib/utils'
import { jobPhase, SectionEvalBadge } from '../evaluation-progress'
import { OBJECTIVE_QUESTION_TOTAL } from '../lib/answers'
import { formatBand } from '../lib/band'
import { cefrLevel } from '../lib/cefr'
import { ENTER, staggerStyle } from '../lib/motion'
import { SKILL_BAND_FIELD, SKILL_KEYS, SKILL_META, type SkillKey } from '../lib/skill'
import { isSectionNotAttempted } from '../lib/status'
import { BandScale } from './ui/band-scale'
import { Panel, PanelBody, PanelHeader, PanelTitle } from './ui/panel'

type SkillMatrixProps = {
  attempt: AttemptDetailRead
}

function jobsFor(attempt: AttemptDetailRead, skill: SkillKey): EvaluationJobRead[] {
  if (skill === 'listening' || skill === 'reading') return []
  return attempt.evaluation_jobs.filter((job) => job.section_type === skill)
}

function rawFor(attempt: AttemptDetailRead, skill: SkillKey): number | null {
  if (skill === 'listening') return attempt.listening_raw
  if (skill === 'reading') return attempt.reading_raw
  return null
}

export function SkillMatrix({ attempt }: SkillMatrixProps) {
  return (
    <Panel className={ENTER} style={staggerStyle(1)}>
      <PanelHeader>
        <PanelTitle>Skills</PanelTitle>
        <p className='font-manrope text-sm tabular-nums text-muted-foreground'>
          Overall {formatBand(attempt.overall_band)}
        </p>
      </PanelHeader>
      <PanelBody className='mt-3 space-y-1'>
        {SKILL_KEYS.map((skill, index) => (
          <SkillRow
            key={skill}
            attempt={attempt}
            skill={skill}
            index={index}
          />
        ))}
      </PanelBody>
    </Panel>
  )
}

function SkillRow({
  attempt,
  skill,
  index,
}: {
  attempt: AttemptDetailRead
  skill: SkillKey
  index: number
}) {
  const meta = SKILL_META[skill]
  const Icon = meta.icon
  const band = attempt[SKILL_BAND_FIELD[skill]]
  const raw = rawFor(attempt, skill)
  const evalJobs = jobsFor(attempt, skill)
  const evalPhase = jobPhase(evalJobs)
  const showEval =
    evalPhase === 'queued' || evalPhase === 'scoring' || evalPhase === 'failed'
  const notAttempted = isSectionNotAttempted(band, attempt.status)
  const cefr = cefrLevel(band)

  return (
    <Link
      to='.'
      search={(prev) => ({ ...prev, tab: skill })}
      replace
      className={cn(
        'group grid items-center gap-3 rounded-xl px-2 py-3 transition-colors duration-150',
        'hover:bg-muted/50 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
        'sm:grid-cols-[9.5rem_minmax(0,1fr)_auto]',
        ENTER,
      )}
      style={staggerStyle(index)}
    >
      <div className='flex min-w-0 items-center gap-3'>
        <div
          className={cn(
            'flex size-9 shrink-0 items-center justify-center rounded-lg',
            meta.surface,
          )}
        >
          <Icon className={cn('size-4', meta.accent)} />
        </div>
        <div className='min-w-0'>
          <p className='text-sm font-medium text-foreground'>{meta.label}</p>
          {!notAttempted && !showEval && raw != null && (
            <p className='text-[11px] tabular-nums text-muted-foreground'>
              {raw}/{OBJECTIVE_QUESTION_TOTAL} correct
            </p>
          )}
        </div>
      </div>

      <div className='min-w-0'>
        {showEval ? (
          <SectionEvalBadge jobs={evalJobs} />
        ) : notAttempted ? (
          <p className='text-sm text-muted-foreground'>Not attempted</p>
        ) : (
          <BandScale band={band} label={meta.label} barClass={meta.bar} />
        )}
      </div>

      <div className='flex items-center justify-end gap-2'>
        {!notAttempted && !showEval && (
          <>
            <span className='font-manrope text-lg font-semibold tracking-tight tabular-nums text-foreground'>
              {formatBand(band)}
            </span>
            {cefr && (
              <span className='hidden text-[11px] font-medium text-muted-foreground sm:inline'>
                {cefr}
              </span>
            )}
          </>
        )}
        <ChevronRight className='size-4 text-muted-foreground opacity-0 transition-opacity duration-150 group-hover:opacity-100' />
      </div>
    </Link>
  )
}
