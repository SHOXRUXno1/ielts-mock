import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { LogOut, MonitorSmartphone } from 'lucide-react'
import { toast } from 'sonner'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  fetchDevices,
  fetchDevicesSummary,
  revokeAllSessions,
  type DevicesStatusFilter,
} from '@/lib/api/devices'
import { ActiveDeviceCard } from './components/active-device-card'
import { DeviceStatCards } from './components/device-stat-cards'
import { DevicesHistoryTable } from './components/devices-history-table'

export function Devices() {
  const [statusFilter, setStatusFilter] =
    useState<DevicesStatusFilter>('all')

  const queryClient = useQueryClient()

  const summaryQuery = useQuery({
    queryKey: ['devices', 'summary'],
    queryFn: fetchDevicesSummary,
    refetchInterval: 15_000,
  })

  const onlineQuery = useQuery({
    queryKey: ['devices', 'online'],
    queryFn: () => fetchDevices({ status: 'online', days: 7, limit: 50 }),
    refetchInterval: 15_000,
  })

  const sessionsQuery = useQuery({
    queryKey: ['devices', 'list', statusFilter],
    queryFn: () => fetchDevices({ status: statusFilter, days: 7, limit: 200 }),
    refetchInterval: 15_000,
  })

  const revokeAllMutation = useMutation({
    mutationFn: revokeAllSessions,
    onSuccess: (data) => {
      toast.success(`Revoked ${data.revoked} session(s)`)
      void queryClient.invalidateQueries({ queryKey: ['devices'] })
    },
    onError: () => toast.error('Failed to revoke sessions'),
  })

  const sessions = sessionsQuery.data ?? []
  const onlineSessions = onlineQuery.data ?? []

  return (
    <>
      <Header fixed>
        <Search className='me-auto' />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main className='flex flex-1 flex-col gap-6'>
        <div className='flex flex-wrap items-end justify-between gap-3'>
          <div>
            <h2 className='text-2xl font-bold tracking-tight'>Devices</h2>
            <p className='text-muted-foreground'>
              See who signed into the admin panel, from which device, and when
              they left.
            </p>
          </div>
          <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant='destructive' size='sm'>
                  <LogOut size={14} className='mr-1.5' />
                  Sign out all other devices
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Sign out all other devices?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will immediately end all admin sessions except your
                    current one. Other admins will need to sign in again.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => revokeAllMutation.mutate()}
                    disabled={revokeAllMutation.isPending}
                  >
                    {revokeAllMutation.isPending ? 'Revoking…' : 'Sign out all'}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
        </div>

        <DeviceStatCards
          summary={summaryQuery.data}
          isLoading={summaryQuery.isLoading}
        />

        <section className='space-y-3'>
          <div className='flex items-center justify-between gap-2'>
            <h3 className='text-sm font-semibold tracking-tight'>
              Active now
            </h3>
            <span className='text-xs text-muted-foreground'>
              Updates every 15s
            </span>
          </div>

          {onlineQuery.isLoading ? (
            <div className='grid gap-3 md:grid-cols-2'>
              <Skeleton className='h-28 rounded-xl' />
              <Skeleton className='h-28 rounded-xl' />
            </div>
          ) : onlineSessions.length > 0 ? (
            <div className='grid gap-3 md:grid-cols-2'>
              {onlineSessions.map((session) => (
                <ActiveDeviceCard key={session.id} session={session} />
              ))}
            </div>
          ) : (
            <div className='flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed bg-muted/20 py-12 text-center'>
              <div className='flex size-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground'>
                <MonitorSmartphone className='size-6' />
              </div>
              <p className='font-medium'>No one is online</p>
              <p className='max-w-sm text-sm text-muted-foreground'>
                Active admin sessions appear here. Closing the tab marks the
                device offline after 1 hour of inactivity.
              </p>
            </div>
          )}
        </section>

        <section className='flex flex-1 flex-col gap-3'>
          <div className='flex flex-wrap items-center justify-between gap-3'>
            <h3 className='text-sm font-semibold tracking-tight'>
              Session history
            </h3>
            <div className='flex items-center rounded-lg border p-0.5 gap-0.5'>
              {(
                [
                  ['all', 'All'],
                  ['online', 'Online'],
                  ['ended', 'Ended'],
                ] as const
              ).map(([value, label]) => (
                <Button
                  key={value}
                  size='sm'
                  variant={statusFilter === value ? 'default' : 'ghost'}
                  className='h-7 px-3 text-xs'
                  onClick={() => setStatusFilter(value)}
                >
                  {label}
                </Button>
              ))}
            </div>
          </div>

          <DevicesHistoryTable
            data={sessions}
            isLoading={sessionsQuery.isLoading}
          />
        </section>
      </Main>
    </>
  )
}
