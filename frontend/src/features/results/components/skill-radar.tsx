import type { AttemptDetailRead } from '@/lib/api/attempts'
import { BAND_MAX } from '../lib/band'
import { ENTER } from '../lib/motion'
import { SKILL_BAND_FIELD, SKILL_CSS_VAR, SKILL_KEYS, type SkillKey } from '../lib/skill'
import { Panel, PanelBody, PanelHeader, PanelTitle } from '@/components/report'

type SkillRadarProps = {
  attempt: AttemptDetailRead
}

const LABEL: Record<SkillKey, string> = {
  listening: 'Listen',
  reading: 'Read',
  writing: 'Write',
  speaking: 'Speak',
}

/** Clockwise from the top, matching SKILL_KEYS. */
const ANGLE_DEG: Record<SkillKey, number> = {
  listening: -90,
  reading: 0,
  writing: 90,
  speaking: 180,
}

const WIDTH = 320
const HEIGHT = 288
const CX = WIDTH / 2
const CY = HEIGHT / 2
const RADIUS = 104
const RING_COUNTS = 3

function polar(radius: number, angleDeg: number): { x: number; y: number } {
  const rad = (angleDeg * Math.PI) / 180
  return { x: CX + radius * Math.cos(rad), y: CY + radius * Math.sin(rad) }
}

function ringPath(radius: number): string {
  return (
    SKILL_KEYS.map((key, index) => {
      const { x, y } = polar(radius, ANGLE_DEG[key])
      return `${index === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`
    }).join(' ') + ' Z'
  )
}

export function SkillRadar({ attempt }: SkillRadarProps) {
  const points = SKILL_KEYS.map((key) => {
    const band = attempt[SKILL_BAND_FIELD[key]] ?? 0
    const radius = RADIUS * Math.max(0, Math.min(1, band / BAND_MAX))
    return { key, band, ...polar(radius, ANGLE_DEG[key]) }
  })
  const valuePath =
    points
      .map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
      .join(' ') + ' Z'

  return (
    <Panel className={ENTER}>
      <PanelHeader>
        <PanelTitle>Score shape</PanelTitle>
      </PanelHeader>
      <PanelBody className='mt-2 flex justify-center'>
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          width={WIDTH}
          height={HEIGHT}
          className='max-w-full'
          role='img'
          aria-label='Score shape'
        >
          {Array.from({ length: RING_COUNTS }, (_, i) => (
            <path
              key={i}
              d={ringPath(((i + 1) / RING_COUNTS) * RADIUS)}
              fill='none'
              className='stroke-border'
              strokeWidth='1'
            />
          ))}
          {SKILL_KEYS.map((key) => {
            const end = polar(RADIUS, ANGLE_DEG[key])
            return (
              <line
                key={key}
                x1={CX}
                y1={CY}
                x2={end.x}
                y2={end.y}
                className='stroke-border'
                strokeWidth='1'
              />
            )
          })}
          <path
            d={valuePath}
            fill='var(--primary)'
            fillOpacity='0.15'
            stroke='var(--primary)'
            strokeWidth='2'
          />
          {points.map((p) => (
            <circle
              key={p.key}
              cx={p.x}
              cy={p.y}
              r='4'
              fill={SKILL_CSS_VAR[p.key]}
              stroke='var(--card)'
              strokeWidth='2'
            />
          ))}
          {SKILL_KEYS.map((key) => {
            const label = polar(RADIUS + 22, ANGLE_DEG[key])
            return (
              <text
                key={key}
                x={label.x}
                y={label.y}
                textAnchor='middle'
                dominantBaseline='middle'
                className='fill-muted-foreground'
                fontSize='12'
              >
                {LABEL[key]}
              </text>
            )
          })}
        </svg>
      </PanelBody>
    </Panel>
  )
}
