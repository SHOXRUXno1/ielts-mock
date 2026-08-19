import { BookOpen, TrendingUp, Trophy } from 'lucide-react'
import { SectionLabel, StatTile } from '@/components/report'
import { ENTER } from '@/features/results/lib/motion'
import { formatBand } from '@/features/results/lib/band'

type PerformancePanelProps = {
  testsTaken: number
  avgBand: number | null
  bestBand: number | null
}

export function PerformancePanel({
  testsTaken,
  avgBand,
  bestBand,
}: PerformancePanelProps) {
  return (
    <div className={ENTER}>
      <SectionLabel className='mb-3'>Performance</SectionLabel>
      <div className='grid grid-cols-1 gap-4 sm:grid-cols-3'>
        <StatTile icon={BookOpen} label='Tests taken' value={testsTaken} />
        <StatTile icon={TrendingUp} label='Average band' value={formatBand(avgBand)} />
        <StatTile icon={Trophy} label='Best band' value={formatBand(bestBand)} />
      </div>
    </div>
  )
}
