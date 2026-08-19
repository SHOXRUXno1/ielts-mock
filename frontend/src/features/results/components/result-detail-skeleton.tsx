import { Skeleton } from '@/components/ui/skeleton'
import { Panel } from '@/components/report'

export function ResultDetailSkeleton() {
  return (
    <div className='flex flex-1 flex-col gap-6' aria-busy='true' aria-label='Loading result'>
      <div className='space-y-3'>
        <Skeleton className='h-8 w-32' />
        <Panel padding='md'>
          <div className='grid gap-6 lg:grid-cols-[auto_minmax(0,1fr)] lg:items-center'>
            <div className='space-y-3'>
              <Skeleton className='h-16 w-28' />
              <Skeleton className='h-1.5 w-44' />
            </div>
            <div className='min-w-0 space-y-4'>
              <Skeleton className='h-7 w-72 max-w-full' />
              <div className='grid gap-3 sm:grid-cols-3'>
                <Skeleton className='h-10 w-full' />
                <Skeleton className='h-10 w-full' />
                <Skeleton className='h-10 w-full' />
              </div>
              <Skeleton className='h-8 w-28' />
            </div>
          </div>
        </Panel>
      </div>
      <Skeleton className='h-11 w-full' />
      <div className='grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]'>
        <Panel padding='md'>
          <Skeleton className='mb-4 h-5 w-28' />
          <Skeleton className='h-64 w-full rounded-xl' />
        </Panel>
        <Panel padding='md'>
          <Skeleton className='mb-4 h-5 w-16' />
          <div className='space-y-3'>
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className='h-12 w-full' />
            ))}
          </div>
        </Panel>
      </div>
      <div className='grid gap-6 lg:grid-cols-2'>
        <Panel padding='md'>
          <Skeleton className='mb-4 h-5 w-20' />
          <div className='space-y-3'>
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className='h-8 w-full' />
            ))}
          </div>
        </Panel>
        <Panel padding='md'>
          <Skeleton className='mb-4 h-5 w-36' />
          <div className='space-y-3'>
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className='h-8 w-full' />
            ))}
          </div>
        </Panel>
      </div>
    </div>
  )
}
