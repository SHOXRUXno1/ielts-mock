import {
  ArrowDownRight,
  ArrowUpRight,
  GitCommitHorizontal,
  Info,
  Scale,
  type LucideIcon,
} from 'lucide-react'
import type { AttemptDetailRead } from '@/lib/api/attempts'
import { formatBand } from '../lib/band'
import { formatRoundingExample, profileInsights } from '../lib/insights'
import { ENTER, staggerStyle } from '../lib/motion'
import { SKILL_META } from '../lib/skill'
import { Panel, PanelBody, PanelHeader, PanelTitle } from '@/components/report'

type InsightsPanelProps = {
  attempt: AttemptDetailRead
}

export function InsightsPanel({ attempt }: InsightsPanelProps) {
  const insights = profileInsights(attempt)
  const rounding = formatRoundingExample(insights)

  return (
    <Panel className={ENTER} style={staggerStyle(2)}>
      <PanelHeader>
        <PanelTitle>Insights</PanelTitle>
      </PanelHeader>
      <PanelBody className='mt-4 space-y-3'>
        {insights.strongest && (
          <InsightRow
            icon={ArrowUpRight}
            label='Strongest'
            value={`${SKILL_META[insights.strongest.key].label} ${formatBand(insights.strongest.band)}`}
          />
        )}
        {insights.weakest && (
          <InsightRow
            icon={ArrowDownRight}
            label='Weakest'
            value={`${SKILL_META[insights.weakest.key].label} ${formatBand(insights.weakest.band)}`}
          />
        )}
        {insights.spread != null && (
          <InsightRow
            icon={GitCommitHorizontal}
            label='Spread'
            value={formatBand(insights.spread)}
          />
        )}
        {insights.even != null && (
          <InsightRow
            icon={Scale}
            label='Profile'
            value={insights.even ? 'Even across skills' : 'Uneven — one skill is pulling the overall down'}
          />
        )}
        <InsightRow
          icon={Info}
          label='Overall'
          value={
            rounding
              ? `Average of all four skills (skipped count as 0), rounded to the nearest 0.5. ${rounding}.`
              : 'Average of all four skills (skipped count as 0), rounded to the nearest 0.5.'
          }
        />
      </PanelBody>
    </Panel>
  )
}

function InsightRow({
  icon: Icon,
  label,
  value,
}: {
  icon: LucideIcon
  label: string
  value: string
}) {
  return (
    <div className='flex items-start gap-3'>
      <div className='mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted'>
        <Icon className='size-3.5 text-muted-foreground' />
      </div>
      <div className='min-w-0'>
        <p className='text-[11px] font-medium tracking-wider text-muted-foreground uppercase'>
          {label}
        </p>
        <p className='text-sm leading-relaxed text-foreground'>{value}</p>
      </div>
    </div>
  )
}
