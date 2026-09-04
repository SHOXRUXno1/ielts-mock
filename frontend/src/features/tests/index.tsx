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
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { fetchTests } from '@/lib/api/tests'
import { type Test } from './data/schema'
import { TestsDialogs } from './components/tests-dialogs'
import { TestsPrimaryButtons } from './components/tests-primary-buttons'
import { TestsProvider } from './components/tests-provider'
import { TestsTable } from './components/tests-table'

type StatusFilter = 'all' | 'published' | 'draft'
type TypeFilter = 'all' | 'academic' | 'general'

// Same palette + hash as the row book-dot, so chip and row agree at a glance.
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
  for (let i = 0; i < slug.length; i++) hash = (hash * 31 + slug.charCodeAt(i)) | 0
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
  return Array.from(map.values()).sort((a, b) => a.label.localeCompare(b.label))
}

function StatTile({
  label,
  value,
  hint,
}: {
  label: string
  value: number | string
  hint?: string
}) {
  return (
    <Card className='flex flex-col gap-1 p-4'>
      <div className='text-xs uppercase tracking-wide text-muted-foreground'>
        {label}
      </div>
      <div className='text-2xl font-semibold tabular-nums'>{value}</div>
      {hint && <div className='text-xs text-muted-foreground'>{hint}</div>}
    </Card>
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

  const stats = useMemo(() => {
    const total = tests.length
    const published = tests.filter((t) => t.is_published).length
    return {
      total,
      published,
      drafts: total - published,
      books: books.length,
    }
  }, [tests, books])

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

        <div className='grid grid-cols-2 gap-3 sm:grid-cols-4'>
          <StatTile label='Total' value={stats.total} />
          <StatTile
            label='Published'
            value={stats.published}
            hint={`${stats.total ? Math.round((stats.published / stats.total) * 100) : 0}% of catalogue`}
          />
          <StatTile label='Drafts' value={stats.drafts} />
          <StatTile
            label='Books'
            value={stats.books}
            hint='distinct sources'
          />
        </div>

        {books.length > 0 && (
          <div className='flex flex-wrap items-center gap-1.5'>
            <button
              type='button'
              onClick={() => setBookFilter('all')}
              className={cn(
                'h-7 rounded-full border px-3 text-xs transition-colors',
                bookFilter === 'all'
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-input bg-background hover:bg-muted',
              )}
            >
              All books
              <span className='ml-1.5 text-[10px] opacity-70'>{tests.length}</span>
            </button>
            {books.map((book) => {
              const active = bookFilter === book.slug
              return (
                <button
                  key={book.slug}
                  type='button'
                  onClick={() => setBookFilter(book.slug)}
                  className={cn(
                    'h-7 rounded-full border px-3 text-xs transition-colors inline-flex items-center gap-1.5',
                    active
                      ? 'border-foreground bg-foreground text-background'
                      : 'border-input bg-background hover:bg-muted',
                  )}
                >
                  <span
                    className={cn('h-1.5 w-1.5 rounded-full', bookDotClass(book.slug))}
                    aria-hidden
                  />
                  {book.label}
                  <span className='text-[10px] opacity-70'>{book.count}</span>
                </button>
              )
            })}
          </div>
        )}

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
      </Main>

      <TestsDialogs />
    </TestsProvider>
  )
}
