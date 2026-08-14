import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearch as useRouteSearch } from '@tanstack/react-router'
import { Search as SearchIcon } from 'lucide-react'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { fetchStudents } from '@/lib/api/students'
import { StudentsDialogs } from './components/students-dialogs'
import { StudentsProvider } from './components/students-provider'
import { StudentsPrimaryButtons } from './components/students-primary-buttons'
import { StudentsTable } from './components/students-table'

type ActiveFilter = 'all' | 'active'

function StudentsPageContent() {
  const { q } = useRouteSearch({ strict: false }) as { q?: string }
  const [search, setSearch] = useState(q ?? '')
  const [activeFilter, setActiveFilter] = useState<ActiveFilter>('all')

  const { data: students = [], isLoading } = useQuery({
    queryKey: ['students', search, activeFilter],
    queryFn: () => fetchStudents({
      search: search || undefined,
      is_active: activeFilter === 'active' ? true : undefined,
    }),
  })

  return (
    <>
      <Header fixed>
        <Search className='me-auto' />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main className='flex flex-1 flex-col gap-4 sm:gap-6'>
        <div className='flex flex-wrap items-end justify-between gap-2'>
          <div>
            <h2 className='text-2xl font-bold tracking-tight'>Students</h2>
            <p className='text-muted-foreground'>
              Manage student accounts and their test access.
            </p>
          </div>
          <StudentsPrimaryButtons />
        </div>

        <div className='flex items-center gap-3'>
          <div className='relative max-w-xs w-full'>
            <SearchIcon size={14} className='absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground' />
            <Input
              placeholder='Search by name or login…'
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className='pl-8'
            />
          </div>

          <div className='flex items-center rounded-lg border p-0.5 gap-0.5'>
            <Button
              size='sm'
              variant={activeFilter === 'active' ? 'default' : 'ghost'}
              className='h-7 px-3 text-xs'
              onClick={() => setActiveFilter('active')}
            >
              Active
            </Button>
            <Button
              size='sm'
              variant={activeFilter === 'all' ? 'default' : 'ghost'}
              className='h-7 px-3 text-xs'
              onClick={() => setActiveFilter('all')}
            >
              All
            </Button>
          </div>
        </div>

        <StudentsTable data={students} isLoading={isLoading} />
      </Main>

      <StudentsDialogs />
    </>
  )
}

export function Students() {
  return (
    <StudentsProvider>
      <StudentsPageContent />
    </StudentsProvider>
  )
}
