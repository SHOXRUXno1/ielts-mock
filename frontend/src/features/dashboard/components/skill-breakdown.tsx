import {
  BookOpen,
  Headphones,
  Lightbulb,
  Mic,
  PenLine,
  type LucideIcon,
} from 'lucide-react'
import type { SkillStat } from '@/lib/api/admin-dashboard'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { cn } from '@/lib/utils'

const SKILL_META: Record<
  SkillStat['section'],
  { label: string; icon: LucideIcon }
> = {
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

export function SkillBreakdown({ skills }: { skills: SkillStat[] }) {
  const scored = skills.filter((s) => s.avg_band != null)
  const weakest = scored.reduce<SkillStat | null>(
    (min, s) => (min == null || s.avg_band! < min.avg_band! ? s : min),
    null,
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className='text-base'>Skill performance</CardTitle>
        <CardDescription>Average band per section · last 30 days</CardDescription>
      </CardHeader>
      <CardContent>
        {scored.length === 0 ? (
          <p className='py-8 text-center text-sm text-muted-foreground'>
            No scored sections in the last 30 days.
          </p>
        ) : (
          <>
            <div className='space-y-3'>
              {skills.map((skill) => {
                const meta = SKILL_META[skill.section]
                const Icon = meta.icon
                const band = skill.avg_band
                return (
                  <div key={skill.section} className='flex items-center gap-3'>
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
                        'w-16 shrink-0 text-right text-sm font-semibold tabular-nums',
                        band != null ? bandText(band) : 'text-muted-foreground',
                      )}
                    >
                      {band != null ? band.toFixed(1) : '—'}
                    </span>
                  </div>
                )
              })}
            </div>
            {weakest != null && scored.length > 1 && (
              <div className='mt-4 flex items-start gap-2 rounded-md bg-muted/50 px-3 py-2 text-xs text-muted-foreground'>
                <Lightbulb className='mt-0.5 size-3.5 shrink-0 text-amber-500' />
                <span>
                  <span className='font-medium text-foreground'>
                    {SKILL_META[weakest.section].label}
                  </span>{' '}
                  is the weakest skill ({weakest.avg_band!.toFixed(1)}) — likely a
                  focus area for your students.
                </span>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
