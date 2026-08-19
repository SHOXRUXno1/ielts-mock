import { AtSign, Clock, Phone } from 'lucide-react'
import { BandValue, Metric, Panel } from '@/components/report'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { ENTER } from '@/features/results/lib/motion'
import { loginKind } from '../lib/profile-stats'

type ProfileHeaderProps = {
  name: string
  initials: string
  login?: string
  avgBand: number | null
  sessionUntil: string
}

export function ProfileHeader({
  name,
  initials,
  login,
  avgBand,
  sessionUntil,
}: ProfileHeaderProps) {
  const LoginIcon = login && loginKind(login) === 'phone' ? Phone : AtSign

  return (
    <Panel className={ENTER}>
      <div className='flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between'>
        <div className='flex min-w-0 flex-col gap-4 sm:flex-row sm:items-center'>
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
              <Badge variant='outline' className='rounded-lg'>
                Active
              </Badge>
            </div>
            <div className='grid gap-3 sm:grid-cols-2'>
              {login && <Metric icon={LoginIcon} label='Login' value={login} />}
              <Metric icon={Clock} label='Session valid until' value={sessionUntil} />
            </div>
          </div>
        </div>

        <div className='shrink-0 space-y-1'>
          <p className='text-xs font-medium tracking-wider text-muted-foreground uppercase'>
            Overall average
          </p>
          <BandValue
            band={avgBand}
            label='Overall average'
            size='lg'
          />
        </div>
      </div>
    </Panel>
  )
}
