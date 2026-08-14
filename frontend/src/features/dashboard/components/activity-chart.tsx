import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ActivityPoint } from '@/lib/api/admin-dashboard'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

function formatDay(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return `${d.getMonth() + 1}/${d.getDate()}`
}

type TooltipEntry = { payload: ActivityPoint }

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: TooltipEntry[]
}) {
  if (!active || !payload || payload.length === 0) return null
  const point = payload[0].payload
  const d = new Date(point.date + 'T00:00:00')
  return (
    <div className='rounded-md border bg-background px-3 py-2 text-xs shadow-md'>
      <p className='font-medium'>
        {d.toLocaleDateString(undefined, {
          weekday: 'short',
          month: 'short',
          day: 'numeric',
        })}
      </p>
      <p className='text-muted-foreground'>
        {point.attempts_count} attempt{point.attempts_count !== 1 ? 's' : ''}
      </p>
    </div>
  )
}

export function ActivityChart({ data }: { data: ActivityPoint[] }) {
  const total = data.reduce((sum, d) => sum + d.attempts_count, 0)
  const todayKey = new Date().toISOString().slice(0, 10)

  return (
    <Card>
      <CardHeader>
        <CardTitle className='flex flex-wrap items-baseline gap-2 text-base'>
          <span>Activity</span>
          <span className='text-sm font-normal text-muted-foreground'>
            last 30 days · {total} attempt{total !== 1 ? 's' : ''}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {total === 0 ? (
          <p className='py-12 text-center text-sm text-muted-foreground'>
            No activity in the last 30 days.
          </p>
        ) : (
          <ResponsiveContainer width='100%' height={220}>
            <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <XAxis
                dataKey='date'
                stroke='#888888'
                fontSize={11}
                tickLine={false}
                axisLine={false}
                minTickGap={24}
                tickFormatter={formatDay}
              />
              <YAxis
                stroke='#888888'
                fontSize={11}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
                width={32}
              />
              <Tooltip
                cursor={{ fill: 'currentColor', opacity: 0.06 }}
                content={<ChartTooltip />}
              />
              <Bar dataKey='attempts_count' radius={[3, 3, 0, 0]}>
                {data.map((entry) => (
                  <Cell
                    key={entry.date}
                    className={
                      entry.date === todayKey
                        ? 'fill-primary'
                        : 'fill-primary/40'
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
