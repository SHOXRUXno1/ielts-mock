import { Panel } from '@/components/report'
import { Skeleton } from '@/components/ui/skeleton'

export function DashboardSkeleton() {
  return (
    <div className='space-y-6'>
      <div className='space-y-2'>
        <Skeleton className='h-8 w-64' />
        <Skeleton className='h-4 w-40' />
      </div>
      <Panel>
        <div className='grid gap-6 lg:grid-cols-[auto_minmax(0,1fr)]'>
          <div className='space-y-4'>
            <Skeleton className='h-16 w-28' />
            <Skeleton className='h-1.5 w-56' />
          </div>
          <div className='space-y-4'>
            <div className='grid gap-3 sm:grid-cols-3'>
              <Skeleton className='h-12 rounded-lg' />
              <Skeleton className='h-12 rounded-lg' />
              <Skeleton className='h-12 rounded-lg' />
            </div>
            <Skeleton className='h-[110px] w-full rounded-xl' />
          </div>
        </div>
      </Panel>
      <Panel>
        <Skeleton className='mb-4 h-5 w-16' />
        <div className='space-y-3'>
          <Skeleton className='h-14 rounded-xl' />
          <Skeleton className='h-14 rounded-xl' />
          <Skeleton className='h-14 rounded-xl' />
          <Skeleton className='h-14 rounded-xl' />
        </div>
      </Panel>
    </div>
  )
}
