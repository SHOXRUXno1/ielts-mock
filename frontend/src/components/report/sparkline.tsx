type SparklinePoint = {
  x: number
  y: number
}

type SparklineProps = {
  points: SparklinePoint[]
  label: string
  className?: string
}

const WIDTH = 560
const HEIGHT = 110
const PAD = 16

export function Sparkline({ points, label, className }: SparklineProps) {
  if (points.length < 2) return null

  const line = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(' ')
  const area = `${line} L${points[points.length - 1].x.toFixed(1)} ${HEIGHT - PAD} L${points[0].x.toFixed(1)} ${HEIGHT - PAD} Z`

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      preserveAspectRatio='none'
      className={className ?? 'h-[110px] w-full text-primary'}
      role='img'
      aria-label={label}
    >
      <path d={area} fill='currentColor' fillOpacity='0.12' />
      <path d={line} fill='none' stroke='currentColor' strokeWidth='2.5' />
      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r='3.5' fill='currentColor' />
      ))}
    </svg>
  )
}

export const SPARKLINE_WIDTH = WIDTH
export const SPARKLINE_HEIGHT = HEIGHT
export const SPARKLINE_PAD = PAD
