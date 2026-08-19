import { CircleAlert } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ENTER } from '../lib/motion'
import { Panel } from './ui/panel'

type ResultErrorStateProps = {
  onRetry: () => void
}

export function ResultErrorState({ onRetry }: ResultErrorStateProps) {
  return (
    <Panel className={ENTER} padding='md'>
      <div className='flex flex-col items-center justify-center gap-3 py-8 text-center'>
        <div className='flex size-12 items-center justify-center rounded-full bg-destructive/10'>
          <CircleAlert className='size-5 text-destructive' />
        </div>
        <div className='space-y-1'>
          <h3 className='text-base font-semibold text-foreground'>
            Could not load result
          </h3>
          <p className='max-w-sm text-sm leading-relaxed text-muted-foreground'>
            The attempt failed to load. Check your connection and try again.
          </p>
        </div>
        <Button size='sm' variant='outline' className='mt-1 rounded-lg' onClick={onRetry}>
          Try again
        </Button>
      </div>
    </Panel>
  )
}
