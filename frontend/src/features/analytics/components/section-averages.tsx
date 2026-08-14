import {
  BookOpen,
  Headphones,
  Mic,
  PenLine,
  type LucideIcon,
} from 'lucide-react'
import type { AnalyticsSectionAverage } from '@/lib/api/analytics'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { cn } from '@/lib/utils'

const SECTION_META: Record<string, { label: string; icon: LucideIcon }> = {
  listening: { label: 'Listening', icon: Headphones },
  reading: { label: 'Reading', icon: BookOpen },
  writing: { label: 'Writing', icon: PenLine },
  speaking: { label: 'Speaking', icon: Mic },
}

function bandFill(band: number): string {
  if (band >= 8) return 'bg-green-500'
  if (band >= 7) return 'bg-blue-500'
  if (band >= 6) return 'bg-amber-500'
  return 'bg-red-500'
}

function bandText(band: number): string {
  if (band >= 8) return 'text-green-600 dark:text-green-400'
  if (band >= 7) return 'text-blue-600 dark:text-blue-400'
  if (band >= 6) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-600 dark:text-red-400'
}

export function SectionAveragesCard({
  sections,
  days,
}: {
  sections: AnalyticsSectionAverage[]
  days: number
}) {
  const scored = sections.filter((s) => s.avg_band != null)

  return (
    <Card>
      <CardHeader>
        <CardTitle className='text-base'>Section performance</CardTitle>
        <CardDescription>Average band per skill · last {days} days</CardDescription>
      </CardHeader>
      <CardContent>
        {scored.length === 0 ? (
          <p className='py-8 text-center text-sm text-muted-foreground'>
            No scored sections in this period.
          </p>
        ) : (
          <div className='space-y-3'>
            {sections.map((s) => {
              const meta = SECTION_META[s.section]
              if (!meta) return null
              const Icon = meta.icon
              const band = s.avg_band
              return (
                <div key={s.section} className='flex items-center gap-3'>
                  <div className='flex w-28 shrink-0 items-center gap-2'>
                    <Icon className='size-4 text-muted-foreground' />
                    <span className='text-sm font-medium'>{meta.label}</span>
                  </div>
                  <div className='relative h-2.5 flex-1 overflow-hidden rounded-full bg-muted/40'>
                    {band != null && (
                      <div
                        className={cn(
                          'absolute inset-y-0 left-0 rounded-full transition-all',
                          bandFill(band),
                        )}
                        style={{ width: `${(band / 9) * 100}%` }}
                      />
                    )}
                  </div>
                  <span
                    className={cn(
                      'w-12 shrink-0 text-right text-sm font-semibold tabular-nums',
                      band != null ? bandText(band) : 'text-muted-foreground',
                    )}
                  >
                    {band != null ? band.toFixed(1) : '—'}
                  </span>
                  <span className='w-14 shrink-0 text-right text-xs tabular-nums text-muted-foreground'>
                    ({s.count})
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
