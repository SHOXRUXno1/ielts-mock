import { Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { Eye, Clock } from 'lucide-react'
import { getMyResults } from '@/lib/api/student'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

function bandColor(band: number | null): string {
  if (band === null) return ''
  if (band >= 7) return 'text-green-600'
  if (band >= 5.5) return 'text-yellow-600'
  return 'text-red-500'
}

export function StudentResults() {
  const { data: results = [], isLoading } = useQuery({
    queryKey: ['student-results'],
    queryFn: getMyResults,
  })

  return (
    <div className='space-y-6'>
      <div>
        <h1 className='text-2xl font-bold tracking-tight'>My Results</h1>
        <p className='text-muted-foreground'>All your test attempts and scores</p>
      </div>

      {isLoading ? (
        <div className='space-y-3'>
          {[0, 1, 2].map((i) => <Skeleton key={i} className='h-16' />)}
        </div>
      ) : results.length === 0 ? (
        <div className='rounded-xl border border-dashed p-8 text-center'>
          <p className='font-medium text-muted-foreground'>No results yet</p>
          <p className='text-sm text-muted-foreground mt-1'>Complete a test to see your score here</p>
          <Button asChild className='mt-4' variant='outline'>
            <Link to='/student/tests'>Take a Test</Link>
          </Button>
        </div>
      ) : (
        <div className='overflow-hidden rounded-lg border'>
          <table className='w-full text-sm'>
            <thead className='bg-muted/40'>
              <tr>
                <th className='px-4 py-3 text-left font-medium'>Test</th>
                <th className='px-4 py-3 text-left font-medium'>Date</th>
                <th className='px-4 py-3 text-center font-medium'>Overall</th>
                <th className='px-4 py-3 text-center font-medium hidden sm:table-cell'>L</th>
                <th className='px-4 py-3 text-center font-medium hidden sm:table-cell'>R</th>
                <th className='px-4 py-3 text-center font-medium hidden sm:table-cell'>W</th>
                <th className='px-4 py-3 text-center font-medium hidden sm:table-cell'>S</th>
                <th className='px-4 py-3 text-center font-medium'>Status</th>
                <th className='px-4 py-3' />
              </tr>
            </thead>
            <tbody className='divide-y'>
              {results.map((r) => (
                <tr key={r.id} className='bg-background hover:bg-muted/30 transition-colors'>
                  <td className='px-4 py-3 font-medium'>{r.test_title}</td>
                  <td className='px-4 py-3 text-muted-foreground text-xs'>
                    <span className='flex items-center gap-1'>
                      <Clock size={10} />
                      {r.finished_at
                        ? new Date(r.finished_at).toLocaleDateString()
                        : new Date(r.created_at).toLocaleDateString()}
                    </span>
                  </td>
                  <td className={`px-4 py-3 text-center font-bold ${bandColor(r.overall_band)}`}>
                    {r.overall_band ?? '—'}
                  </td>
                  <td className='px-4 py-3 text-center text-muted-foreground hidden sm:table-cell'>{r.listening_band ?? '—'}</td>
                  <td className='px-4 py-3 text-center text-muted-foreground hidden sm:table-cell'>{r.reading_band ?? '—'}</td>
                  <td className='px-4 py-3 text-center text-muted-foreground hidden sm:table-cell'>{r.writing_band ?? '—'}</td>
                  <td className='px-4 py-3 text-center text-muted-foreground hidden sm:table-cell'>{r.speaking_band ?? '—'}</td>
                  <td className='px-4 py-3 text-center'>
                    <Badge variant='outline' className='capitalize text-xs'>{r.status}</Badge>
                  </td>
                  <td className='px-4 py-3'>
                    <Button asChild size='sm' variant='ghost'>
                      <Link to='/student/results/$attemptId' params={{ attemptId: r.id }}>
                        <Eye size={14} />
                      </Link>
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
