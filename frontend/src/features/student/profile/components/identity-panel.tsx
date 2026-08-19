import { Mail, Shield } from 'lucide-react'
import { Metric, Panel } from '@/components/report'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { ENTER } from '@/features/results/lib/motion'

type IdentityPanelProps = {
  name: string
  initials: string
  login?: string
}

export function IdentityPanel({ name, initials, login }: IdentityPanelProps) {
  return (
    <Panel className={ENTER}>
      <div className='flex flex-col gap-4 sm:flex-row sm:items-center'>
        <Avatar className='size-16 rounded-xl'>
          <AvatarFallback className='rounded-xl bg-muted text-lg font-semibold text-foreground'>
            {initials}
          </AvatarFallback>
        </Avatar>
        <div className='min-w-0 space-y-3'>
          <div className='flex flex-wrap items-center gap-2'>
            <h2 className='text-xl font-semibold tracking-tight text-foreground'>
              {name}
            </h2>
            <Badge variant='secondary' className='rounded-lg'>
              Student
            </Badge>
          </div>
          <div className='grid gap-3 sm:grid-cols-2'>
            {login && <Metric icon={Mail} label='Login' value={login} />}
            <Metric icon={Shield} label='Account' value='Student' />
          </div>
        </div>
      </div>
    </Panel>
  )
}
