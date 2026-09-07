import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search as SearchIcon } from 'lucide-react'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { fetchTests } from '@/lib/api/tests'
import { type Test } from './data/schema'
import { BookSidebar } from './components/book-sidebar'
import { TestsDialogs } from './components/tests-dialogs'
import { TestsPrimaryButtons } from './components/tests-primary-buttons'
import { TestsProvider } from './components/tests-provider'
import { TestsTable } from './components/tests-table'

type StatusFilter = 'all' | 'published' | 'draft'
type TypeFilter = 'all' | 'academic' | 'general'

const BOOK_DOT_PALETTE = [
  'bg-teal-500',
  'bg-amber-500',
  'bg-violet-500',
  'bg-rose-500',
  'bg-sky-500',
  'bg-emerald-500',
  'bg-indigo-500',
  'bg-orange-500',
]

function bookDotClass(slug: string): string {
  let hash = 0
  for (let i = 0; i < slug.length; i++)
    hash = (hash * 31 + slug.charCodeAt(i)) | 0
  return BOOK_DOT_PALETTE[Math.abs(hash) % BOOK_DOT_PALETTE.length]
}

type BookOption = { slug: string; label: string; count: number }

function collectBooks(tests: Test[]): BookOption[] {
  const map = new Map<string, BookOption>()
  for (const t of tests) {
    if (!t.book_slug) continue
    const existing = map.get(t.book_slug)
    if (existing) {
      existing.count += 1
    } else {
      map.set(t.book_slug, {
        slug: t.book_slug,
        label: t.book_name ?? t.book_slug,
        count: 1,
      })
    }
  }
  return Array.from(map.values()).sort((a, b) =>
    a.label.localeCompare(b.label),
  )
}

function SegmentedPill<T extends string>({
  value,
  onChange,
  options,
}: {
  value: T
  onChange: (v: T) => void
  options: { value: T; label: string }[]
}) {
  return (
    <div className='flex items-center rounded-lg border p-0.5 gap-0.5'>
      {options.map((opt) => (
        <Button
          key={opt.value}
          size='sm'
          variant={value === opt.value ? 'default' : 'ghost'}
          className='h-7 px-3 text-xs'
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </Button>
      ))}
    </div>
  )
}

export function Tests() {
  const { data: tests = [], isLoading } = useQuery({
    queryKey: ['tests'],
    queryFn: fetchTests,
  })

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('all')
  const [bookFilter, setBookFilter] = useState<string>('all')

  const books = useMemo(() => collectBooks(tests), [tests])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return tests.filter((t) => {
      if (
        q &&
        !t.title.toLowerCase().includes(q) &&
        !(t.book_name ?? '').toLowerCase().includes(q)
      ) {
        return false
      }
      if (statusFilter === 'published' && !t.is_published) return false
      if (statusFilter === 'draft' && t.is_published) return false
      if (typeFilter !== 'all' && t.type !== typeFilter) return false
      if (bookFilter !== 'all' && t.book_slug !== bookFilter) return false
      return true
    })
  }, [tests, search, statusFilter, typeFilter, bookFilter])

  return (
    <TestsProvider>
      <Header fixed>
        <Search className='me-auto' />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>

      <Main className='flex flex-1 flex-col gap-4 sm:gap-5'>
        <div className='flex flex-wrap items-center justify-between gap-2'>
          <h2 className='text-2xl font-bold tracking-tight'>Tests</h2>
          <TestsPrimaryButtons />
        </div>

        <div className='flex gap-5'>
          {/* Book sidebar — desktop only */}
          {books.length > 0 && (
            <BookSidebar
              books={books}
              selected={bookFilter}
              onSelect={setBookFilter}
              totalCount={tests.length}
              dotClass={bookDotClass}
              className='hidden w-52 shrink-0 md:flex'
            />
          )}

          {/* Table area */}
          <div className='min-w-0 flex-1'>
            <TestsTable
              data={filtered}
              isLoading={isLoading}
              totalUnfiltered={tests.length}
              toolbar={
                <>
                  <div className='relative w-full max-w-xs'>
                    <SearchIcon
                      size={14}
                      className='absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground'
                    />
                    <Input
                      placeholder='Search by title or book…'
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      className='pl-8 h-9'
                    />
                  </div>

                  {/* Mobile book filter */}
                  {books.length > 0 && (
                    <Select
                      value={bookFilter}
                      onValueChange={setBookFilter}
                    >
                      <SelectTrigger className='h-9 w-[160px] text-xs md:hidden'>
                        <SelectValue placeholder='All books' />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value='all'>All books</SelectItem>
                        {books.map((b) => (
                          <SelectItem key={b.slug} value={b.slug}>
                            {b.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}

                  <SegmentedPill<StatusFilter>
                    value={statusFilter}
                    onChange={setStatusFilter}
                    options={[
                      { value: 'all', label: 'All' },
                      { value: 'published', label: 'Published' },
                      { value: 'draft', label: 'Drafts' },
                    ]}
                  />
                  <SegmentedPill<TypeFilter>
                    value={typeFilter}
                    onChange={setTypeFilter}
                    options={[
                      { value: 'all', label: 'All types' },
                      { value: 'academic', label: 'Academic' },
                      { value: 'general', label: 'General' },
                    ]}
                  />
                </>
              }
            />
          </div>
        </div>
      </Main>

      <TestsDialogs />
    </TestsProvider>
  )
}
