import { Skeleton } from '@/components/ui/skeleton'

export function ResultDetailSkeleton() {
  return (
    <div className='flex flex-1 flex-col gap-6' aria-busy='true' aria-label='Loading result'>
      <div className='space-y-3'>
        <Skeleton className='h-8 w-32' />
        <div className='rounded-2xl bg-card p-6 shadow-sm ring-1 ring-border'>
          <div className='flex flex-col gap-6 sm:flex-row sm:items-center'>
            <Skeleton className='size-40 shrink-0 rounded-full' />
            <div className='min-w-0 flex-1 space-y-4'>
              <Skeleton className='h-7 w-72 max-w-full' />
              <div className='grid gap-3 sm:grid-cols-3'>
                <Skeleton className='h-10 w-full' />
                <Skeleton className='h-10 w-full' />
                <Skeleton className='h-10 w-full' />
              </div>
              <Skeleton className='h-9 w-28' />
            </div>
          </div>
        </div>
      </div>
      <Skeleton className='h-11 w-full rounded-xl' />
      <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className='rounded-2xl bg-card p-5 shadow-sm ring-1 ring-border'>
            <Skeleton className='mb-4 size-9 rounded-lg' />
            <Skeleton className='h-9 w-16' />
            <Skeleton className='mt-3 h-1.5 w-full' />
          </div>
        ))}
      </div>
      <div className='grid gap-4 lg:grid-cols-[1.4fr_1fr]'>
        <div className='rounded-2xl bg-card p-6 shadow-sm ring-1 ring-border'>
          <Skeleton className='mb-4 h-5 w-40' />
          <div className='space-y-3'>
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className='h-6 w-full' />
            ))}
          </div>
        </div>
        <div className='rounded-2xl bg-card p-6 shadow-sm ring-1 ring-border'>
          <Skeleton className='mb-4 h-5 w-24' />
          <div className='space-y-3'>
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className='h-8 w-full' />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
