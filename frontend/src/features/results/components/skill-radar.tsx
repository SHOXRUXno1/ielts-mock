import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
} from 'recharts'
import type { AttemptDetailRead } from '@/lib/api/attempts'
import { BAND_MAX } from '../lib/band'
import { ENTER } from '../lib/motion'
import { SKILL_BAND_FIELD, SKILL_CSS_VAR, SKILL_KEYS, type SkillKey } from '../lib/skill'
import { Panel, PanelBody, PanelHeader, PanelTitle } from './ui/panel'

type SkillRadarProps = {
  attempt: AttemptDetailRead
}

type RadarPoint = {
  skill: string
  key: SkillKey
  value: number
}

function SkillDot({
  cx,
  cy,
  payload,
}: {
  cx?: number
  cy?: number
  payload?: RadarPoint
}) {
  if (cx == null || cy == null || !payload) return null
  return (
    <circle
      cx={cx}
      cy={cy}
      r={4}
      fill={SKILL_CSS_VAR[payload.key]}
      stroke='var(--card)'
      strokeWidth={2}
    />
  )
}

export function SkillRadar({ attempt }: SkillRadarProps) {
  const data: RadarPoint[] = SKILL_KEYS.map((key) => ({
    skill: key === 'listening' ? 'Listen' : key === 'reading' ? 'Read' : key === 'writing' ? 'Write' : 'Speak',
    key,
    value: attempt[SKILL_BAND_FIELD[key]] ?? 0,
  }))

  return (
    <Panel className={ENTER}>
      <PanelHeader>
        <PanelTitle>Score shape</PanelTitle>
      </PanelHeader>
      <PanelBody className='mt-2 flex justify-center'>
        <RadarChart
          width={320}
          height={288}
          data={data}
          cx='50%'
          cy='50%'
          outerRadius='72%'
        >
          <PolarGrid className='stroke-border' />
          <PolarAngleAxis
            dataKey='skill'
            tick={{
              fontSize: 12,
              fill: 'var(--muted-foreground)',
            }}
          />
          <PolarRadiusAxis
            domain={[0, BAND_MAX]}
            tick={false}
            axisLine={false}
          />
          <Radar
            dataKey='value'
            stroke='var(--primary)'
            fill='var(--primary)'
            fillOpacity={0.15}
            strokeWidth={2}
            dot={<SkillDot />}
            isAnimationActive={false}
          />
        </RadarChart>
      </PanelBody>
    </Panel>
  )
}
