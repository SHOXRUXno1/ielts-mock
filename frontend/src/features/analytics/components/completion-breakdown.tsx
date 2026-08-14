import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { CompletionBreakdown } from '@/lib/api/analytics'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

const SEGMENTS = [
  { key: 'completed', label: 'Completed', color: '#22c55e' },
  { key: 'abandoned', label: 'Abandoned', color: '#ef4444' },
  { key: 'in_progress', label: 'In progress', color: '#3b82f6' },
] as const

type PayloadEntry = { name: string; value: number }

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: { payload: PayloadEntry }[]
}) {
  if (!active || !payload || payload.length === 0) return null
  const p = payload[0].payload
  return (
    <div className='rounded-md border bg-background px-3 py-1.5 text-xs shadow-md'>
      <span className='font-medium'>{p.name}</span>:{' '}
      <span className='tabular-nums'>{p.value}</span>
    </div>
  )
}

export function CompletionBreakdownCard({
  data,
}: {
  data: CompletionBreakdown
}) {
  const total = data.completed + data.abandoned + data.in_progress
  const chartData = SEGMENTS.map((s) => ({
    name: s.label,
    value: data[s.key],
    color: s.color,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className='text-base'>Completion breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        {total === 0 ? (
          <p className='py-8 text-center text-sm text-muted-foreground'>
            No attempts in this period.
          </p>
        ) : (
          <div className='flex items-center gap-6'>
            <ResponsiveContainer width={160} height={160}>
              <PieChart>
                <Pie
                  data={chartData}
                  dataKey='value'
                  nameKey='name'
                  cx='50%'
                  cy='50%'
                  innerRadius={42}
                  outerRadius={70}
                  paddingAngle={2}
                  strokeWidth={0}
                >
                  {chartData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
              </PieChart>
            </ResponsiveContainer>

            <div className='flex-1 space-y-3'>
              {SEGMENTS.map((s) => {
                const count = data[s.key]
                const pct = total > 0 ? Math.round((count / total) * 100) : 0
                return (
                  <div key={s.key} className='flex items-center gap-2'>
                    <span
                      className='size-2.5 shrink-0 rounded-full'
                      style={{ background: s.color }}
                    />
                    <span className='flex-1 text-sm'>{s.label}</span>
                    <span className='text-sm font-semibold tabular-nums'>
                      {count}
                    </span>
                    <span className='w-10 text-right text-xs tabular-nums text-muted-foreground'>
                      {pct}%
                    </span>
                  </div>
                )
              })}

              <div className='border-t pt-2'>
                <div className='flex items-center justify-between text-sm'>
                  <span className='text-muted-foreground'>Total</span>
                  <span className='font-semibold tabular-nums'>{total}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
