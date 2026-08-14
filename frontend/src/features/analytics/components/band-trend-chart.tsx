import { useState } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { BandTrendPoint } from '@/lib/api/analytics'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { cn } from '@/lib/utils'

const SERIES = [
  { key: 'overall', label: 'Overall', color: '#6366f1' },
  { key: 'listening', label: 'Listening', color: '#3b82f6' },
  { key: 'reading', label: 'Reading', color: '#10b981' },
  { key: 'writing', label: 'Writing', color: '#f59e0b' },
  { key: 'speaking', label: 'Speaking', color: '#ef4444' },
] as const

function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return `${d.getMonth() + 1}/${d.getDate()}`
}

type PayloadEntry = { payload: BandTrendPoint; color: string; name: string }

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: PayloadEntry[]
  label?: string
}) {
  if (!active || !payload || !label) return null
  const d = new Date(label + 'T00:00:00')
  return (
    <div className='rounded-md border bg-background px-3 py-2 text-xs shadow-md'>
      <p className='mb-1 font-medium'>
        {d.toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        })}
      </p>
      {payload.map((p) =>
        p.payload[p.name as keyof BandTrendPoint] != null ? (
          <p key={p.name} className='flex items-center gap-1.5'>
            <span
              className='inline-block size-2 rounded-full'
              style={{ background: p.color }}
            />
            <span className='text-muted-foreground'>{p.name}:</span>
            <span className='font-semibold tabular-nums'>
              {Number(p.payload[p.name as keyof BandTrendPoint]).toFixed(1)}
            </span>
          </p>
        ) : null,
      )}
    </div>
  )
}

export function BandTrendChart({
  data,
  days,
}: {
  data: BandTrendPoint[]
  days: number
}) {
  const [visible, setVisible] = useState<Record<string, boolean>>({
    overall: true,
    listening: true,
    reading: true,
    writing: true,
    speaking: true,
  })

  const toggle = (key: string) =>
    setVisible((prev) => ({ ...prev, [key]: !prev[key] }))

  const hasData = data.some((p) => p.count > 0)

  return (
    <Card>
      <CardHeader>
        <div className='flex flex-wrap items-start justify-between gap-2'>
          <div>
            <CardTitle className='text-base'>Band trend</CardTitle>
            <CardDescription>
              Average band per {days === 90 ? 'week' : 'day'} · last {days} days
            </CardDescription>
          </div>
          <div className='flex flex-wrap gap-1'>
            {SERIES.map((s) => (
              <Button
                key={s.key}
                size='sm'
                variant='ghost'
                className={cn(
                  'h-6 px-2 text-[10px] gap-1',
                  !visible[s.key] && 'opacity-40',
                )}
                onClick={() => toggle(s.key)}
              >
                <span
                  className='inline-block size-2 rounded-full'
                  style={{ background: s.color }}
                />
                {s.label}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <p className='py-16 text-center text-sm text-muted-foreground'>
            No scored attempts in this period.
          </p>
        ) : (
          <ResponsiveContainer width='100%' height={300}>
            <LineChart
              data={data}
              margin={{ top: 4, right: 8, left: -20, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray='3 3'
                className='stroke-muted/30'
              />
              <XAxis
                dataKey='bucket'
                stroke='#888888'
                fontSize={11}
                tickLine={false}
                axisLine={false}
                minTickGap={28}
                tickFormatter={formatDate}
              />
              <YAxis
                domain={[0, 9]}
                ticks={[3, 5, 7, 9]}
                stroke='#888888'
                fontSize={11}
                tickLine={false}
                axisLine={false}
                width={32}
              />
              <Tooltip content={<ChartTooltip />} />
              <Legend
                verticalAlign='bottom'
                height={0}
                wrapperStyle={{ display: 'none' }}
              />
              {SERIES.map(
                (s) =>
                  visible[s.key] && (
                    <Line
                      key={s.key}
                      type='monotone'
                      dataKey={s.key}
                      name={s.key}
                      stroke={s.color}
                      strokeWidth={s.key === 'overall' ? 2.5 : 1.5}
                      dot={false}
                      connectNulls
                    />
                  ),
              )}
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
