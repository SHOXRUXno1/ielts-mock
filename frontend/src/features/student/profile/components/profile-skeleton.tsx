import { Panel } from '@/components/report'
import { Skeleton } from '@/components/ui/skeleton'

export function ProfileSkeleton() {
  return (
    <div className='space-y-6'>
      <div className='space-y-2'>
        <Skeleton className='h-8 w-32' />
        <Skeleton className='h-4 w-64' />
      </div>
      <Panel>
        <div className='flex items-center gap-4'>
          <Skeleton className='size-16 rounded-xl' />
          <div className='space-y-2'>
            <Skeleton className='h-6 w-40' />
            <Skeleton className='h-4 w-48' />
          </div>
        </div>
      </Panel>
      <div className='grid grid-cols-1 gap-4 sm:grid-cols-3'>
        <Skeleton className='h-20 rounded-2xl' />
        <Skeleton className='h-20 rounded-2xl' />
        <Skeleton className='h-20 rounded-2xl' />
      </div>
    </div>
  )
}
