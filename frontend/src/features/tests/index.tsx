import { useQuery } from '@tanstack/react-query'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { fetchTests } from '@/lib/api/tests'
import { TestsDialogs } from './components/tests-dialogs'
import { TestsPrimaryButtons } from './components/tests-primary-buttons'
import { TestsProvider } from './components/tests-provider'
import { TestsTable } from './components/tests-table'

export function Tests() {
  const { data: tests = [], isLoading } = useQuery({
    queryKey: ['tests'],
    queryFn: fetchTests,
  })

  return (
    <TestsProvider>
      <Header fixed>
        <Search className='me-auto' />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main className='flex flex-1 flex-col gap-4 sm:gap-6'>
        <div className='flex flex-wrap items-end justify-between gap-2'>
          <div>
            <h2 className='text-2xl font-bold tracking-tight'>Tests</h2>
            <p className='text-muted-foreground'>
              Manage IELTS mock tests and their sections here.
            </p>
          </div>
          <TestsPrimaryButtons />
        </div>
        <TestsTable data={tests} isLoading={isLoading} />
      </Main>

      <TestsDialogs />
    </TestsProvider>
  )
}
