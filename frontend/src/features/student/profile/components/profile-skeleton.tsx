import { Panel } from '@/components/report'
import { Skeleton } from '@/components/ui/skeleton'

export function ProfileSkeleton() {
  return (
    <div className='space-y-6'>
      <div className='space-y-2'>
        <Skeleton className='h-8 w-32' />
        <Skeleton className='h-4 w-72' />
      </div>

      <Panel>
        <div className='flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between'>
          <div className='flex items-center gap-4'>
            <Skeleton className='size-16 rounded-xl' />
            <div className='space-y-2'>
              <Skeleton className='h-6 w-40' />
              <Skeleton className='h-4 w-48' />
            </div>
          </div>
          <Skeleton className='h-12 w-24' />
        </div>
      </Panel>

      <div className='grid gap-6 lg:grid-cols-[minmax(0,1fr)_18rem]'>
        <div className='space-y-6'>
          <Panel>
            <Skeleton className='mb-4 h-5 w-32' />
            <div className='space-y-3'>
              <Skeleton className='h-14 rounded-xl' />
              <Skeleton className='h-14 rounded-xl' />
              <Skeleton className='h-14 rounded-xl' />
              <Skeleton className='h-14 rounded-xl' />
            </div>
          </Panel>
          <div className='grid grid-cols-1 gap-4 sm:grid-cols-2'>
            <Skeleton className='h-20 rounded-2xl' />
            <Skeleton className='h-20 rounded-2xl' />
            <Skeleton className='h-20 rounded-2xl' />
            <Skeleton className='h-20 rounded-2xl' />
          </div>
        </div>
        <div className='space-y-6'>
          <Panel>
            <Skeleton className='mb-4 h-5 w-28' />
            <Skeleton className='h-10 w-full rounded-lg' />
            <Skeleton className='mt-4 h-10 w-full rounded-lg' />
          </Panel>
          <Skeleton className='h-16 rounded-2xl' />
        </div>
      </div>
    </div>
  )
}
