import { describe, expect, it } from 'vitest'
import type { Question, Section, Test } from '../data/schema'
import { computeWizardStatuses } from './wizard-status'

const test: Test = {
  id: 't3',
  title: 'Cambridge IELTS 15 – Test 3',
  description: null,
  is_published: false,
  type: 'academic',
  book_name: 'Cambridge IELTS 15',
  book_slug: 'cambridge-ielts-15',
  test_number: 3,
  created_at: '',
  updated_at: '',
}

function speakingSection(id: string, order: number): Section {
  return {
    id,
    test_id: 't3',
    type: 'speaking',
    order,
    audio_url: null,
    passage: null,
    audioscript: null,
    title: null,
    passage_subtitle: null,
    question_count: 0,
    question_groups: [],
    created_at: '',
    updated_at: '',
  }
}

function speakingQuestion(
  sectionId: string,
  content: Record<string, unknown>,
): Question {
  return {
    id: `${sectionId}-q`,
    section_id: sectionId,
    question_group_id: 'g1',
    order: 1,
    question_type: 'speaking_part',
    content,
    answer_key: null,
    task_number: null,
    min_words: null,
    image_url: null,
    essay_type: null,
    created_at: '',
    updated_at: '',
  }
}

const emptyShells = [
  speakingSection('s30', 30),
  speakingSection('s31', 31),
  speakingSection('s32', 32),
]

describe('computeWizardStatuses — speaking', () => {
  it('is empty when three speaking shells have no prompts', () => {
    const statuses = computeWizardStatuses(test, emptyShells, {})
    expect(statuses[4]).toBe('empty')
  })

  it('is partial when only some parts have prompts', () => {
    const statuses = computeWizardStatuses(test, emptyShells, {
      s30: [
        speakingQuestion('s30', {
          part: 1,
          questions: ['How many languages can you speak?'],
        }),
      ],
    })
    expect(statuses[4]).toBe('partial')
  })

  it('is complete only when all three parts are authored', () => {
    const statuses = computeWizardStatuses(test, emptyShells, {
      s30: [
        speakingQuestion('s30', {
          part: 1,
          questions: ['How many languages can you speak?'],
        }),
      ],
      s31: [
        speakingQuestion('s31', {
          part: 2,
          cue_card: { topic: 'a website that you bought something from', bullets: [] },
        }),
      ],
      s32: [
        speakingQuestion('s32', {
          part: 3,
          questions: ['Why has online shopping become popular?'],
        }),
      ],
    })
    expect(statuses[4]).toBe('complete')
  })

  it('does not treat an empty questions array as authored', () => {
    const statuses = computeWizardStatuses(test, emptyShells, {
      s30: [speakingQuestion('s30', { part: 1, questions: [] })],
      s31: [speakingQuestion('s31', { part: 2, cue_card: { topic: '', bullets: [] } })],
      s32: [speakingQuestion('s32', { part: 3, questions: ['   '] })],
    })
    expect(statuses[4]).toBe('empty')
  })
})
