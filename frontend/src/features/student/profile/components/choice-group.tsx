import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { cn } from '@/lib/utils'

export type Choice<T extends string> = {
  value: T
  label: string
}

type ChoiceGroupProps<T extends string> = {
  label: string
  value: T
  options: readonly Choice<T>[]
  onChange: (value: T) => void
  className?: string
}

export function ChoiceGroup<T extends string>({
  label,
  value,
  options,
  onChange,
  className,
}: ChoiceGroupProps<T>) {
  return (
    <div className={className}>
      <p className='mb-2 text-xs font-medium tracking-wider text-muted-foreground uppercase'>
        {label}
      </p>
      <RadioGroup
        value={value}
        onValueChange={(next) => onChange(next as T)}
        aria-label={label}
        className='grid grid-cols-3 gap-2'
      >
        {options.map((option) => {
          const selected = option.value === value
          return (
            <label
              key={option.value}
              className={cn(
                'flex cursor-pointer items-center justify-center rounded-lg border px-3 py-2 text-sm font-medium transition-colors',
                'has-focus-visible:ring-2 has-focus-visible:ring-ring has-focus-visible:outline-none',
                selected
                  ? 'border-foreground bg-muted text-foreground'
                  : 'border-border text-muted-foreground hover:bg-muted/50 hover:text-foreground',
              )}
            >
              <RadioGroupItem
                value={option.value}
                className='sr-only'
                aria-label={option.label}
              />
              {option.label}
            </label>
          )
        })}
      </RadioGroup>
    </div>
  )
}
