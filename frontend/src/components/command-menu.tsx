import { useCallback, useMemo, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  BarChart3,
  BookOpen,
  ChevronRight,
  Laptop,
  Loader2,
  Moon,
  Sun,
  Users,
} from 'lucide-react'
import { useSearch } from '@/context/search-provider'
import { useTheme } from '@/context/theme-provider'
import { useAuthStore } from '@/stores/auth-store'
import { fetchTests } from '@/lib/api/tests'
import { fetchResults } from '@/lib/api/attempts'
import type { AttemptListItem } from '@/lib/api/attempts'
import { fetchStudents } from '@/lib/api/students'
import type { StudentRead } from '@/lib/api/students'
import type { Test } from '@/features/tests/data/schema'
import { sidebarDataFor } from './layout/data/sidebar-data'
import {
  Command,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ScrollArea } from './ui/scroll-area'

const CAP = 6

function matches(haystack: string, query: string): boolean {
  const h = haystack.toLowerCase()
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .every((term) => h.includes(term))
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
  })
}

export function CommandMenu() {
  const navigate = useNavigate()
  const { setTheme } = useTheme()
  const { open, setOpen } = useSearch()
  const role = useAuthStore((s) => s.auth.user?.role)
  const [query, setQuery] = useState('')

  const runCommand = useCallback(
    (command: () => unknown) => {
      setOpen(false)
      setQuery('')
      command()
    },
    [setOpen]
  )

  const navData = useMemo(() => sidebarDataFor(role), [role])

  const enabled = open && role === 'admin'

  const { data: tests = [], isFetching: fetchingTests } = useQuery({
    queryKey: ['tests'],
    queryFn: fetchTests,
    enabled,
    staleTime: 60_000,
  })

  const { data: results = [], isFetching: fetchingResults } = useQuery({
    queryKey: ['results'],
    queryFn: () => fetchResults(),
    enabled,
    staleTime: 60_000,
  })

  const { data: students = [], isFetching: fetchingStudents } = useQuery({
    queryKey: ['students', '', 'all'],
    queryFn: () => fetchStudents({}),
    enabled,
    staleTime: 60_000,
  })

  const isFetching = fetchingTests || fetchingResults || fetchingStudents
  const hasQuery = query.trim().length > 0

  const filteredNav = useMemo(() => {
    if (!hasQuery) return navData.navGroups
    return navData.navGroups
      .map((group) => ({
        ...group,
        items: group.items.filter((item) => {
          if (item.url && matches(item.title, query)) return true
          if (item.items?.some((sub) => matches(`${item.title} ${sub.title}`, query)))
            return true
          return false
        }),
      }))
      .filter((g) => g.items.length > 0)
  }, [navData.navGroups, query, hasQuery])

  const filteredTests = useMemo<Test[]>(() => {
    if (!hasQuery || role !== 'admin') return []
    return tests
      .filter((t) =>
        matches(
          [t.title, t.book_name, t.type, t.test_number != null ? `test ${t.test_number}` : '']
            .filter(Boolean)
            .join(' '),
          query
        )
      )
      .slice(0, CAP)
  }, [tests, query, hasQuery, role])

  const filteredResults = useMemo<AttemptListItem[]>(() => {
    if (!hasQuery || role !== 'admin') return []
    return results
      .filter((r) =>
        matches([r.test_title, r.status].join(' '), query)
      )
      .slice(0, CAP)
  }, [results, query, hasQuery, role])

  const filteredStudents = useMemo<StudentRead[]>(() => {
    if (!hasQuery || role !== 'admin') return []
    return students
      .filter((s) =>
        matches(
          [s.full_name, s.login, s.group_name].filter(Boolean).join(' '),
          query
        )
      )
      .slice(0, CAP)
  }, [students, query, hasQuery, role])

  const themeItems = useMemo(() => {
    const items = [
      { label: 'Light', value: 'light' as const, icon: Sun },
      { label: 'Dark', value: 'dark' as const, icon: Moon },
      { label: 'System', value: 'system' as const, icon: Laptop },
    ]
    if (!hasQuery) return items
    return items.filter((i) => matches(i.label, query))
  }, [hasQuery, query])

  const totalResults =
    filteredNav.reduce((sum, g) => sum + g.items.length, 0) +
    filteredTests.length +
    filteredResults.length +
    filteredStudents.length +
    themeItems.length

  const showEmpty = hasQuery && !isFetching && totalResults === 0

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        setOpen(v)
        if (!v) setQuery('')
      }}
    >
      <DialogHeader className='sr-only'>
        <DialogTitle>Command Palette</DialogTitle>
        <DialogDescription>Search for a command to run...</DialogDescription>
      </DialogHeader>
      <DialogContent className='overflow-hidden p-0' showCloseButton>
        <Command
          shouldFilter={false}
          className='**:data-[slot=command-input-wrapper]:h-12 [&_[cmdk-group]:not([hidden])_~[cmdk-group]]:pt-0 [&_[cmdk-input-wrapper]_svg]:h-5 [&_[cmdk-input-wrapper]_svg]:w-5 [&_[cmdk-item]_svg]:h-5 [&_[cmdk-item]_svg]:w-5 **:[[cmdk-group-heading]]:px-2 **:[[cmdk-group-heading]]:font-medium **:[[cmdk-group-heading]]:text-muted-foreground **:[[cmdk-group]]:px-2 **:[[cmdk-input]]:h-12 **:[[cmdk-item]]:px-2 **:[[cmdk-item]]:py-3'
        >
          <CommandInput
            placeholder='Type a command or search...'
            value={query}
            onValueChange={setQuery}
          />
          <CommandList>
            <ScrollArea type='hover' className='h-72 pe-1'>
              {/* Loading indicator */}
              {hasQuery && isFetching && (
                <div className='flex items-center justify-center gap-2 py-6 text-sm text-muted-foreground'>
                  <Loader2 className='size-4 animate-spin' />
                  Searching...
                </div>
              )}

              {/* Empty state */}
              {showEmpty && (
                <div className='py-6 text-center text-sm text-muted-foreground'>
                  No results found.
                </div>
              )}

              {/* Navigation */}
              {filteredNav.map((group) => (
                <CommandGroup key={group.title} heading={group.title}>
                  {group.items.map((navItem, i) => {
                    if (navItem.url)
                      return (
                        <CommandItem
                          key={`${navItem.url}-${i}`}
                          value={navItem.title}
                          onSelect={() => {
                            runCommand(() => navigate({ to: navItem.url }))
                          }}
                        >
                          <div className='flex size-4 items-center justify-center'>
                            <ArrowRight className='size-2 text-muted-foreground/80' />
                          </div>
                          {navItem.title}
                        </CommandItem>
                      )

                    return navItem.items
                      ?.filter(
                        (sub) =>
                          !hasQuery ||
                          matches(`${navItem.title} ${sub.title}`, query)
                      )
                      .map((subItem, j) => (
                        <CommandItem
                          key={`${navItem.title}-${subItem.url}-${j}`}
                          value={`${navItem.title}-${subItem.url}`}
                          onSelect={() => {
                            runCommand(() => navigate({ to: subItem.url }))
                          }}
                        >
                          <div className='flex size-4 items-center justify-center'>
                            <ArrowRight className='size-2 text-muted-foreground/80' />
                          </div>
                          {navItem.title} <ChevronRight /> {subItem.title}
                        </CommandItem>
                      ))
                  })}
                </CommandGroup>
              ))}

              {/* Tests */}
              {filteredTests.length > 0 && (
                <>
                  <CommandSeparator />
                  <CommandGroup heading='Tests'>
                    {filteredTests.map((t) => (
                      <CommandItem
                        key={t.id}
                        value={`test-${t.id}`}
                        onSelect={() => {
                          runCommand(() =>
                            navigate({
                              to: '/tests/$testId',
                              params: { testId: t.id },
                            })
                          )
                        }}
                      >
                        <BookOpen className='size-4 text-muted-foreground' />
                        <span className='flex-1 truncate'>{t.title}</span>
                        <span className='ml-auto text-xs text-muted-foreground'>
                          {[
                            t.book_name,
                            t.test_number != null ? `#${t.test_number}` : null,
                            t.is_published ? 'Published' : 'Draft',
                          ]
                            .filter(Boolean)
                            .join(' · ')}
                        </span>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </>
              )}

              {/* Students */}
              {filteredStudents.length > 0 && (
                <>
                  <CommandSeparator />
                  <CommandGroup heading='Students'>
                    {filteredStudents.map((s) => (
                      <CommandItem
                        key={s.id}
                        value={`student-${s.id}`}
                        onSelect={() => {
                          runCommand(() =>
                            navigate({
                              to: '/students',
                              search: { q: s.login },
                            })
                          )
                        }}
                      >
                        <Users className='size-4 text-muted-foreground' />
                        <span className='flex-1 truncate'>{s.full_name}</span>
                        <span className='ml-auto text-xs text-muted-foreground'>
                          {[s.login, s.group_name].filter(Boolean).join(' · ')}
                        </span>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </>
              )}

              {/* Results */}
              {filteredResults.length > 0 && (
                <>
                  <CommandSeparator />
                  <CommandGroup heading='Results'>
                    {filteredResults.map((r) => (
                      <CommandItem
                        key={r.id}
                        value={`result-${r.id}`}
                        onSelect={() => {
                          runCommand(() =>
                            navigate({
                              to: '/results/$attemptId',
                              params: { attemptId: r.id },
                            })
                          )
                        }}
                      >
                        <BarChart3 className='size-4 text-muted-foreground' />
                        <span className='flex-1 truncate'>{r.test_title}</span>
                        <span className='ml-auto text-xs text-muted-foreground'>
                          {[
                            r.status.replace(/_/g, ' '),
                            r.overall_band != null ? `Band ${r.overall_band}` : null,
                            formatDate(r.created_at),
                          ]
                            .filter(Boolean)
                            .join(' · ')}
                        </span>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </>
              )}

              {/* Theme */}
              {themeItems.length > 0 && (
                <>
                  <CommandSeparator />
                  <CommandGroup heading='Theme'>
                    {themeItems.map((item) => (
                      <CommandItem
                        key={item.value}
                        value={item.value}
                        onSelect={() =>
                          runCommand(() => setTheme(item.value))
                        }
                      >
                        <item.icon
                          className={
                            item.value === 'dark' ? 'scale-90' : undefined
                          }
                        />
                        <span>{item.label}</span>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </>
              )}
            </ScrollArea>
          </CommandList>
        </Command>
      </DialogContent>
    </Dialog>
  )
}
