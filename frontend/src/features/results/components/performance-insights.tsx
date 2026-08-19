import { ArrowDownRight, ArrowUpRight, GitCommitHorizontal, Info } from 'lucide-react'
import type { AttemptDetailRead } from '@/lib/api/attempts'
import { formatBand } from '../lib/band'
import { SKILL_KEYS, SKILL_META, type SkillKey } from '../lib/skill'

type PerformanceInsightsProps = {
  attempt: AttemptDetailRead
}

const SKILL_BAND: Record<SkillKey, keyof AttemptDetailRead> = {
  listening: 'listening_band',
  reading: 'reading_band',
  writing: 'writing_band',
  speaking: 'speaking_band',
}

export function PerformanceInsights({ attempt }: PerformanceInsightsProps) {
  const scored = SKILL_KEYS.map((key) => ({
    key,
    band: attempt[SKILL_BAND[key]] as number | null,
  })).filter((row): row is { key: SkillKey; band: number } => row.band != null)

  const strongest = scored.reduce<(typeof scored)[number] | null>(
    (best, row) => (!best || row.band > best.band ? row : best),
    null,
  )
  const weakest = scored.reduce<(typeof scored)[number] | null>(
    (worst, row) => (!worst || row.band < worst.band ? row : worst),
    null,
  )
  const spread =
    strongest && weakest ? strongest.band - weakest.band : null

  return (
    <div className='rounded-2xl bg-card p-6 shadow-sm ring-1 ring-border'>
      <h3 className='text-base font-semibold text-foreground'>Insights</h3>
      <div className='mt-4 space-y-3'>
        {strongest && (
          <InsightRow
            icon={ArrowUpRight}
            label='Strongest'
            value={`${SKILL_META[strongest.key].label} ${formatBand(strongest.band)}`}
          />
        )}
        {weakest && scored.length > 1 && (
          <InsightRow
            icon={ArrowDownRight}
            label='Weakest'
            value={`${SKILL_META[weakest.key].label} ${formatBand(weakest.band)}`}
          />
        )}
        {spread != null && scored.length > 1 && (
          <InsightRow
            icon={GitCommitHorizontal}
            label='Spread'
            value={formatBand(spread)}
          />
        )}
        <InsightRow
          icon={Info}
          label='Overall'
          value='Average of scored sections, rounded to the nearest 0.5. At least three sections required.'
        />
      </div>
    </div>
  )
}

function InsightRow({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Info
  label: string
  value: string
}) {
  return (
    <div className='flex items-start gap-2.5'>
      <div className='mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-md bg-muted'>
        <Icon className='size-3.5 text-muted-foreground' />
      </div>
      <div className='min-w-0'>
        <p className='text-[10px] font-medium tracking-wider text-muted-foreground uppercase'>
          {label}
        </p>
        <p className='text-sm leading-relaxed text-foreground'>{value}</p>
      </div>
    </div>
  )
}
