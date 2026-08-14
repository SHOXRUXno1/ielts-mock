import { useMutation, useQueryClient } from '@tanstack/react-query'
import { LogOut } from 'lucide-react'
import { toast } from 'sonner'
import type { AdminSession } from '@/lib/api/devices'
import { revokeSession } from '@/lib/api/devices'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { relativeTime } from '../lib/format'
import { DeviceIcon } from './device-icon'

type ActiveDeviceCardProps = {
  session: AdminSession
}

export function ActiveDeviceCard({ session }: ActiveDeviceCardProps) {
  const title = [session.browser, session.os_name].filter(Boolean).join(' · ')
  const subtitle = session.ip_address || 'Unknown IP'
  const queryClient = useQueryClient()

  const revokeMutation = useMutation({
    mutationFn: () => revokeSession(session.id),
    onSuccess: () => {
      toast.success('Session revoked')
      void queryClient.invalidateQueries({ queryKey: ['devices'] })
    },
    onError: () => toast.error('Failed to revoke session'),
  })

  return (
    <Card
      className={cn(
        'relative overflow-hidden transition-shadow hover:shadow-md',
        session.is_current && 'ring-2 ring-primary/40'
      )}
    >
      <CardContent className='flex items-start gap-4 py-5'>
        <div
          className={cn(
            'flex size-12 shrink-0 items-center justify-center rounded-2xl',
            session.is_current
              ? 'bg-primary/10 text-primary'
              : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
          )}
        >
          <DeviceIcon deviceType={session.device_type} size={24} />
        </div>

        <div className='min-w-0 flex-1'>
          <div className='flex flex-wrap items-center gap-2'>
            <h3 className='truncate font-semibold tracking-tight'>
              {title || 'Unknown device'}
            </h3>
            {session.is_current && (
              <Badge variant='secondary' className='font-normal'>
                This device
              </Badge>
            )}
          </div>
          <p className='mt-0.5 truncate text-sm text-muted-foreground'>
            {subtitle}
            <span className='mx-1.5 text-muted-foreground/50'>·</span>
            Signed in {relativeTime(session.login_at)}
          </p>
          <p className='mt-1 truncate text-xs text-muted-foreground'>
            {session.actor_name || session.actor_login}
            <span className='mx-1.5'>·</span>
            Active {relativeTime(session.last_seen_at)}
          </p>
        </div>

        <div className='flex shrink-0 flex-col items-end gap-2 pt-1'>
          <div className='flex items-center gap-1.5'>
            <span className='relative flex size-2.5'>
              <span className='absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-75' />
              <span className='relative inline-flex size-2.5 rounded-full bg-emerald-500' />
            </span>
            <span className='text-xs font-medium text-emerald-600 dark:text-emerald-400'>
              Online
            </span>
          </div>
          {!session.is_current && (
            <Button
              variant='ghost'
              size='sm'
              className='h-7 px-2 text-xs text-destructive hover:bg-destructive/10 hover:text-destructive'
              onClick={() => revokeMutation.mutate()}
              disabled={revokeMutation.isPending}
            >
              <LogOut size={12} className='mr-1' />
              {revokeMutation.isPending ? 'Revoking…' : 'Sign out'}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
