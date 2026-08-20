type Props = {
  min: number
  max: number
}

function Chip({ n }: { n: number }) {
  return (
    <span
      data-q-chip
      data-q-n={n}
      className='inline-flex min-w-[1.15em] justify-center'
    >
      {n}
    </span>
  )
}

/** "Question 9" / "Questions 5–7" — IELTS range, not 5–6–7. */
export function QuestionRangeTitle({ min, max }: Props) {
  if (min === max) {
    return (
      <p className='text-[15px] font-bold text-primary'>
        Question <Chip n={min} />
      </p>
    )
  }

  return (
    <p className='text-[15px] font-bold text-primary'>
      Questions <Chip n={min} />–<Chip n={max} />
      {Array.from({ length: Math.max(0, max - min - 1) }, (_, i) => min + 1 + i).map(
        (n) => (
          <span key={n} data-q-chip data-q-n={n} className='sr-only' />
        ),
      )}
    </p>
  )
}
