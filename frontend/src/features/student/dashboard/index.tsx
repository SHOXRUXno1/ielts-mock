import { Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { BookOpen, Trophy, TrendingUp, Clock } from 'lucide-react'
import { getDashboard } from '@/lib/api/student'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

function StatCard({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <Card>
      <CardContent className='flex items-center gap-4 pt-6'>
        <div className='flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10'>
          <Icon size={18} className='text-primary' />
        </div>
        <div>
          <p className='text-2xl font-bold'>{value}</p>
          <p className='text-xs text-muted-foreground'>{label}</p>
        </div>
      </CardContent>
    </Card>
  )
}

function bandBadgeVariant(band: number | null) {
  if (band === null) return 'secondary'
  if (band >= 7) return 'default'
  if (band >= 5.5) return 'outline'
  return 'secondary'
}

export function StudentDashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['student-dashboard'],
    queryFn: getDashboard,
  })

  if (isLoading) {
    return (
      <div className='space-y-6'>
        <Skeleton className='h-8 w-48' />
        <div className='grid gap-4 sm:grid-cols-3'>
          {[0, 1, 2].map((i) => <Skeleton key={i} className='h-20' />)}
        </div>
      </div>
    )
  }

  return (
    <div className='space-y-8'>
      <div>
        <h1 className='text-2xl font-bold tracking-tight'>Dashboard</h1>
        <p className='text-muted-foreground'>Your IELTS progress overview</p>
      </div>

      <div className='grid gap-4 sm:grid-cols-3'>
        <StatCard icon={BookOpen} label='Tests Taken' value={String(data?.tests_taken ?? 0)} />
        <StatCard icon={TrendingUp} label='Average Band' value={data?.avg_band != null ? String(data.avg_band) : '—'} />
        <StatCard icon={Trophy} label='Best Band' value={data?.best_band != null ? String(data.best_band) : '—'} />
      </div>

      {/* Quick link to tests */}
      <div className='flex items-center justify-between'>
        <h2 className='text-lg font-semibold'>Quick Access</h2>
        <Button asChild variant='outline' size='sm'>
          <Link to='/student/tests'>View All Tests</Link>
        </Button>
      </div>

      {/* Recent results */}
      {data?.recent && data.recent.length > 0 && (
        <div>
          <h2 className='text-lg font-semibold mb-3'>Recent Attempts</h2>
          <div className='space-y-2'>
            {data.recent.map((a) => (
              <div key={a.id} className='flex items-center justify-between rounded-lg border bg-card px-4 py-3'>
                <div>
                  <p className='text-sm font-medium'>{a.test_title}</p>
                  <p className='text-xs text-muted-foreground flex items-center gap-1'>
                    <Clock size={11} />
                    {a.finished_at
                      ? new Date(a.finished_at).toLocaleDateString()
                      : new Date(a.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className='flex items-center gap-2'>
                  {a.overall_band != null ? (
                    <Badge variant={bandBadgeVariant(a.overall_band)}>Band {a.overall_band}</Badge>
                  ) : (
                    <Badge variant='secondary'>{a.status}</Badge>
                  )}
                  <Button asChild size='sm' variant='ghost'>
                    <Link to='/student/results/$attemptId' params={{ attemptId: a.id }}>View</Link>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {data?.recent?.length === 0 && (
        <div className='rounded-xl border border-dashed p-8 text-center'>
          <BookOpen size={32} className='mx-auto mb-3 text-muted-foreground' />
          <p className='font-medium'>No tests taken yet</p>
          <p className='text-sm text-muted-foreground mb-4'>Start your first IELTS practice test</p>
          <Button asChild>
            <Link to='/student/tests'>Browse Tests</Link>
          </Button>
        </div>
      )}
    </div>
  )
}
