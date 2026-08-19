import {
  SPARKLINE_HEIGHT,
  SPARKLINE_PAD,
  SPARKLINE_WIDTH,
} from '@/components/report'
import { BAND_MAX, formatBand } from '@/features/results/lib/band'

export type TrendSample = {
  band: number
  date: string
}

export function sparklinePoints(
  values: number[],
): Array<{ x: number; y: number }> {
  if (values.length === 0) return []
  const span = Math.max(1, values.length - 1)
  return values.map((value, index) => {
    const x =
      SPARKLINE_PAD + (index * (SPARKLINE_WIDTH - SPARKLINE_PAD * 2)) / span
    const pct = Math.max(0, Math.min(1, value / BAND_MAX))
    const y =
      SPARKLINE_HEIGHT -
      SPARKLINE_PAD -
      pct * (SPARKLINE_HEIGHT - SPARKLINE_PAD * 2)
    return { x, y }
  })
}

export function trendSummary(samples: TrendSample[]): string {
  if (samples.length < 2) {
    return 'Not enough attempts to show a trend'
  }
  const first = samples[0].band
  const last = samples[samples.length - 1].band
  const delta = last - first
  const direction =
    delta > 0 ? 'up' : delta < 0 ? 'down' : 'unchanged'
  return `${samples.length} attempts, ${formatBand(first)} to ${formatBand(last)}, ${direction}`
}
