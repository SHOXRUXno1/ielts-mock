import { describe, expect, it } from 'vitest'
import { render } from 'vitest-browser-react'
import { WritingFeedbackView } from './writing-feedback-view'
import type { WritingFeedbackResult } from '@/lib/api/feedback'

const SAMPLE_FEEDBACK: WritingFeedbackResult = {
  overall_band: 6.5,
  task_achievement: { band: 7.0, feedback: 'Task addressed well.' },
  coherence_cohesion: { band: 6.0, feedback: 'Generally organised.' },
  lexical_resource: { band: 6.5, feedback: 'Adequate vocabulary range.' },
  grammatical_range: { band: 6.5, feedback: 'Mix of simple and complex structures.' },
  strengths: ['Clear overview statement', 'Good use of comparisons'],
  improvements: ['Include more specific data', 'Avoid repetition'],
  errors: [
    {
      quote: 'informations',
      type: 'grammar',
      correction: 'information',
      explanation: "'information' is an uncountable noun in English.",
    },
    {
      quote: 'teh',
      type: 'spelling',
      correction: 'the',
      explanation: 'Spelling error.',
    },
  ],
  word_count: 165,
}

function hasText(text: string): boolean {
  const bodyText = document.body.textContent
  return bodyText !== null && bodyText !== undefined && bodyText.includes(text)
}

describe('WritingFeedbackView', () => {
  it('renders the overall band score', async () => {
    await render(
      <WritingFeedbackView feedback={SAMPLE_FEEDBACK} essayText='' />,
    )
    expect(hasText('6.5')).toBe(true)
  })

  it('renders criterion labels', async () => {
    await render(
      <WritingFeedbackView feedback={SAMPLE_FEEDBACK} essayText='' />,
    )
    expect(hasText('Task Achievement')).toBe(true)
    expect(hasText('Coherence & Cohesion')).toBe(true)
    expect(hasText('Lexical Resource')).toBe(true)
    expect(hasText('Grammatical Range')).toBe(true)
  })

  it('renders strengths', async () => {
    await render(
      <WritingFeedbackView feedback={SAMPLE_FEEDBACK} essayText='' />,
    )
    expect(hasText('Clear overview statement')).toBe(true)
    expect(hasText('Good use of comparisons')).toBe(true)
  })

  it('renders improvements', async () => {
    await render(
      <WritingFeedbackView feedback={SAMPLE_FEEDBACK} essayText='' />,
    )
    expect(hasText('Include more specific data')).toBe(true)
    expect(hasText('Avoid repetition')).toBe(true)
  })

  it('renders error corrections list', async () => {
    // Quotes must appear in essayText to survive sanitization
    const essay =
      'The chart shows informations about employment. teh data reveals trends.'
    await render(
      <WritingFeedbackView feedback={SAMPLE_FEEDBACK} essayText={essay} />,
    )
    expect(hasText('informations')).toBe(true)
    expect(hasText('information')).toBe(true)
    expect(hasText('teh')).toBe(true)
    expect(hasText('the')).toBe(true)
  })

  it('drops error quotes that are not in the essay', async () => {
    const feedback: WritingFeedbackResult = {
      ...SAMPLE_FEEDBACK,
      errors: [
        {
          quote: 'not-in-essay',
          type: 'grammar',
          correction: 'x',
          explanation: 'missing',
        },
        {
          quote: 'informations',
          type: 'grammar',
          correction: 'information',
          explanation: 'ok',
        },
      ],
    }
    const essay = 'The chart shows informations about employment.'
    await render(<WritingFeedbackView feedback={feedback} essayText={essay} />)
    expect(hasText('not-in-essay')).toBe(false)
    expect(hasText('informations')).toBe(true)
  })

  it('renders annotated essay when essayText provided', async () => {
    const essay =
      'The chart shows informations about employment. teh data reveals trends.'

    await render(
      <WritingFeedbackView feedback={SAMPLE_FEEDBACK} essayText={essay} />,
    )

    expect(hasText('Your Essay (annotated)')).toBe(true)
    const marks = document.querySelectorAll('mark')
    expect(marks.length).toBeGreaterThan(0)
  })

  it('renders plain text when no errors — no mark elements', async () => {
    const noErrors: WritingFeedbackResult = {
      ...SAMPLE_FEEDBACK,
      errors: [],
    }

    await render(
      <WritingFeedbackView feedback={noErrors} essayText='Clean text here.' />,
    )

    const marks = document.querySelectorAll('mark')
    expect(marks.length).toBe(0)
  })

  it('handles null criteria gracefully without crashing', async () => {
    const partial: WritingFeedbackResult = {
      overall_band: 5.0,
      task_achievement: null,
      coherence_cohesion: null,
      lexical_resource: null,
      grammatical_range: null,
      strengths: [],
      improvements: [],
      errors: [],
      word_count: 0,
    }

    await render(<WritingFeedbackView feedback={partial} essayText='' />)
    expect(hasText('5.0')).toBe(true)
    // None of the criterion labels should appear since all are null
    expect(hasText('Task Achievement')).toBe(false)
  })
})
