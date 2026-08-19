import { BookOpen, Calendar, Timer, Trophy } from 'lucide-react'
import { SectionLabel, StatTile } from '@/components/report'
import { formatBand } from '@/features/results/lib/band'
import { ENTER } from '@/features/results/lib/motion'

type LifetimePanelProps = {
  mockTests: number
  practiceSessions: number
  bestBand: number | null
  activeSince: string | null
}

function formatActiveSince(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function LifetimePanel({
  mockTests,
  practiceSessions,
  bestBand,
  activeSince,
}: LifetimePanelProps) {
  return (
    <div className={ENTER}>
      <SectionLabel className='mb-3'>Lifetime</SectionLabel>
      <div className='grid grid-cols-1 gap-4 sm:grid-cols-2'>
        <StatTile icon={BookOpen} label='Mock tests' value={mockTests} />
        <StatTile icon={Timer} label='Practice sessions' value={practiceSessions} />
        <StatTile icon={Trophy} label='Best band' value={formatBand(bestBand)} />
        <StatTile
          icon={Calendar}
          label='Active since'
          value={formatActiveSince(activeSince)}
        />
      </div>
    </div>
  )
}
