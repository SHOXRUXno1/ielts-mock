import { BookOpen, TrendingUp, Trophy } from 'lucide-react'
import {
  BandScale,
  BandValue,
  Metric,
  Panel,
  Sparkline,
} from '@/components/report'
import type { BandTrendPoint, DashboardResponse } from '@/lib/api/student'
import { ENTER } from '@/features/results/lib/motion'
import { formatBand } from '@/features/results/lib/band'
import { sparklinePoints, trendSummary } from '../lib/trend'

type DashboardHeroProps = {
  data: DashboardResponse
}

export function DashboardHero({ data }: DashboardHeroProps) {
  const samples: BandTrendPoint[] = Array.isArray(data.band_trend)
    ? data.band_trend
    : []
  const points = sparklinePoints(samples.map((sample) => sample.band))
  const label = trendSummary(samples)

  return (
    <Panel className={ENTER}>
      <div className='grid gap-6 lg:grid-cols-[auto_minmax(0,1fr)] lg:items-center'>
        <div className='space-y-4'>
          <BandValue band={data.avg_band} label='Overall' size='display' />
          <BandScale band={data.avg_band} label='Overall' className='max-w-56' />
        </div>
        <div className='min-w-0 space-y-4'>
          <div className='grid gap-3 sm:grid-cols-3'>
            <Metric
              icon={BookOpen}
              label='Tests taken'
              value={String(data.tests_taken)}
            />
            <Metric
              icon={TrendingUp}
              label='Average'
              value={formatBand(data.avg_band)}
            />
            <Metric
              icon={Trophy}
              label='Best'
              value={formatBand(data.best_band)}
            />
          </div>
          {points.length >= 2 ? (
            <Sparkline points={points} label={label} />
          ) : (
            <p className='text-sm text-muted-foreground'>
              Complete more tests to see your trend
            </p>
          )}
        </div>
      </div>
    </Panel>
  )
}
