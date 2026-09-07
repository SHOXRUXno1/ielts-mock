import { cn } from '@/lib/utils'

type BookOption = { slug: string; label: string; count: number }

type BookSidebarProps = {
  books: BookOption[]
  selected: string
  onSelect: (slug: string) => void
  totalCount: number
  dotClass: (slug: string) => string
  className?: string
}

export function BookSidebar({
  books,
  selected,
  onSelect,
  totalCount,
  dotClass,
  className,
}: BookSidebarProps) {
  return (
    <nav className={cn('flex flex-col gap-0.5', className)}>
      <SidebarItem
        active={selected === 'all'}
        onClick={() => onSelect('all')}
        label='All books'
        count={totalCount}
      />
      <div className='my-1 h-px bg-border' />
      {books.map((book) => (
        <SidebarItem
          key={book.slug}
          active={selected === book.slug}
          onClick={() => onSelect(book.slug)}
          label={book.label}
          count={book.count}
          dot={dotClass(book.slug)}
        />
      ))}
    </nav>
  )
}

function SidebarItem({
  active,
  onClick,
  label,
  count,
  dot,
}: {
  active: boolean
  onClick: () => void
  label: string
  count: number
  dot?: string
}) {
  return (
    <button
      type='button'
      onClick={onClick}
      className={cn(
        'flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-left text-sm transition-colors',
        active
          ? 'bg-muted font-medium text-foreground'
          : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground',
      )}
    >
      {dot && (
        <span
          className={cn('h-2 w-2 shrink-0 rounded-full', dot)}
          aria-hidden
        />
      )}
      <span className='min-w-0 truncate'>{label}</span>
      <span
        className={cn(
          'ml-auto shrink-0 text-xs tabular-nums',
          active ? 'text-foreground/70' : 'text-muted-foreground/60',
        )}
      >
        {count}
      </span>
    </button>
  )
}
