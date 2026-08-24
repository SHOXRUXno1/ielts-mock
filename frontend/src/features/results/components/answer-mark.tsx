import { cn } from '@/lib/utils'
import { splitChoiceLetters } from '../lib/answers'

type Tone = 'wrong' | 'right' | 'plain'

type Props = {
  value: string
  tone: Tone
  /**
   * Whether this question labels its options with letters. Off by default, so
   * a value is only ever shown as an option letter when the question actually
   * has them — Roman numerals and ordinary words stay as written.
   */
  optionLetters?: boolean
  /**
   * The answer key, when the value being shown is the candidate's own. Each
   * option letter is then coloured on its own, so a half-right "Choose TWO"
   * pair shows which of the two letters earned its mark.
   */
  matchAgainst?: string | null
}

/**
 * How a scored answer is shown in a review table.
 *
 * Option letters sit in a mark, never under a strikethrough: a line through
 * "B" lands on the middle bar and the letter reads as "D".
 */
export function AnswerMark({
  value,
  tone,
  optionLetters = false,
  matchAgainst,
}: Props) {
  const letters = optionLetters ? splitChoiceLetters(value) : null
  const keyLetters =
    optionLetters && matchAgainst ? splitChoiceLetters(matchAgainst) : null
  if (!letters) {
    if (tone === 'wrong') {
      return <span className='text-muted-foreground line-through'>{value}</span>
    }
    return (
      <span
        className={cn(
          'font-medium',
          tone === 'right' ? 'text-success-foreground' : 'text-foreground',
        )}
      >
        {value}
      </span>
    )
  }

  return (
    <span className='inline-flex items-center gap-1'>
      {letters.map((letter, index) => {
        const letterTone: Tone = keyLetters
          ? keyLetters.includes(letter)
            ? 'right'
            : 'wrong'
          : tone
        return (
          <span
            key={`${letter}-${index}`}
            className={cn(
              'inline-flex size-7 items-center justify-center rounded-md',
              'font-sans text-[15px] leading-none font-semibold',
              letterTone === 'wrong' &&
                'bg-destructive/10 text-destructive ring-1 ring-destructive/35',
              letterTone === 'right' &&
                'bg-success text-success-foreground ring-1 ring-success-foreground/25',
              letterTone === 'plain' && 'bg-muted text-foreground',
            )}
          >
            {letter}
          </span>
        )
      })}
    </span>
  )
}
