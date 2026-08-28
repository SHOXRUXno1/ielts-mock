import { describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import type { Question, QuestionGroup, Section } from '../data/schema'
import { SectionLivePreview } from './section-live-preview'

vi.mock('@/lib/api/attempts', () => ({
  mediaUrl: (url: string) => url,
}))

function makeQuestion(): Question {
  return {
    id: 'q10',
    section_id: 's1',
    question_group_id: 'g1',
    order: 10,
    question_type: 'mcq',
    content: {
      question: "Which map shows the correct location of the seller's house?",
      options: ['A', 'B', 'C'],
    },
    answer_key: { correct: 'B' },
    task_number: null,
    min_words: null,
    image_url: '/media/images/practice_b_t1_listening_map.png',
    essay_type: null,
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
  }
}

function makeSection(question: Question): Section {
  const group: QuestionGroup = {
    id: 'g1',
    section_id: 's1',
    order: 2,
    question_type: 'mcq',
    instruction: 'Choose the correct letter, A, B or C.',
    subtitle: null,
    options_shared: null,
    questions: [question],
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
  }
  return {
    id: 's1',
    test_id: 't1',
    type: 'listening',
    order: 1,
    audio_url: null,
    passage: null,
    audioscript: null,
    title: 'Part 1',
    passage_subtitle: null,
    question_count: 1,
    question_groups: [group],
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
  }
}

describe('Section live preview MCQ image', () => {
  it('shows the saved question image', async () => {
    const screen = await render(
      <SectionLivePreview section={makeSection(makeQuestion())} />,
    )

    const el = screen.container.querySelector('img') as HTMLImageElement
    expect(el).toBeTruthy()
    expect(el.getAttribute('src')).toBe(
      '/media/images/practice_b_t1_listening_map.png',
    )
  })

  it('uses the live draft image while editing', async () => {
    const screen = await render(
      <SectionLivePreview
        section={makeSection(makeQuestion())}
        drafts={{
          g1: {
            groupId: 'g1',
            questionType: 'mcq',
            instruction: 'Choose the correct letter, A, B or C.',
            questions: [
              {
                id: 'q10',
                order: 10,
                content: {
                  question:
                    "Which map shows the correct location of the seller's house?",
                  options: ['A', 'B', 'C'],
                },
                answer_key: { correct: 'B' },
                image_url: '/media/images/new-map.png',
              },
            ],
          },
        }}
      />,
    )

    const el = screen.container.querySelector('img') as HTMLImageElement
    expect(el.getAttribute('src')).toBe('/media/images/new-map.png')
  })
})
