type Props = {
  min: number
  max: number
}

/** "Question 9" / "Questions 23–24" with each number as its own flash target. */
export function QuestionRangeTitle({ min, max }: Props) {
  const nums: number[] = []
  for (let n = min; n <= max; n++) nums.push(n)

  return (
    <p className='text-[15px] font-bold text-primary'>
      {min === max ? 'Question ' : 'Questions '}
      {nums.map((n, i) => (
        <span key={n}>
          {i > 0 && '–'}
          <span
            data-q-chip
            data-q-n={n}
            className='inline-flex min-w-[1.15em] justify-center'
          >
            {n}
          </span>
        </span>
      ))}
    </p>
  )
}
