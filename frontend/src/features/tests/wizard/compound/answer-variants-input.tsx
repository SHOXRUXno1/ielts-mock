import { useRef, useState } from 'react'
import { X } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

type Props = {
  value: string[]
  onChange: (variants: string[]) => void
  placeholder?: string
  autoFocus?: boolean
  className?: string
}

export function AnswerVariantsInput({
  value,
  onChange,
  placeholder = 'Type and press Enter',
  autoFocus = false,
  className,
}: Props) {
  const [draft, setDraft] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const addVariant = (text: string) => {
    const trimmed = text.trim()
    if (!trimmed) return
    if (value.some((v) => v.toLowerCase() === trimmed.toLowerCase())) return
    onChange([...value, trimmed])
    setDraft('')
  }

  const removeVariant = (index: number) => {
    onChange(value.filter((_, i) => i !== index))
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addVariant(draft)
    } else if (e.key === 'Backspace' && draft === '' && value.length > 0) {
      removeVariant(value.length - 1)
    }
  }

  const handleBlur = () => {
    if (draft.trim()) {
      addVariant(draft)
    }
  }

  return (
    <div
      className={cn(
        'flex min-h-8 flex-wrap items-center gap-1 rounded-md border border-input bg-background px-2 py-1 text-sm ring-offset-background focus-within:ring-1 focus-within:ring-ring',
        className,
      )}
      onClick={() => inputRef.current?.focus()}
    >
      {value.map((variant, i) => (
        <Badge
          key={i}
          variant='secondary'
          className='gap-0.5 py-0 pl-2 pr-1 text-xs'
        >
          {variant}
          <button
            type='button'
            className='ml-0.5 rounded-sm p-0.5 hover:bg-muted'
            onClick={(e) => {
              e.stopPropagation()
              removeVariant(i)
            }}
            aria-label={`Remove ${variant}`}
          >
            <X className='size-3' />
          </button>
        </Badge>
      ))}
      <input
        ref={inputRef}
        type='text'
        className='min-w-[80px] flex-1 bg-transparent outline-none placeholder:text-muted-foreground'
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        placeholder={value.length === 0 ? placeholder : ''}
        autoFocus={autoFocus}
      />
    </div>
  )
}
