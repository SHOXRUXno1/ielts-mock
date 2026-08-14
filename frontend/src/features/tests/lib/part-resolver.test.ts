import { describe, expect, it } from 'vitest'
import type { Question, Section } from '../data/schema'
import {
  clampPart,
  isSectionType,
  partCount,
  partIndexForSection,
  resolvePart,
  sectionsOfType,
} from './part-resolver'

const NOW = new Date().toISOString()

function section(
  id: string,
  type: Section['type'],
  order: number,
  overrides: Partial<Section> = {},
): Section {
  return {
    id,
    test_id: 'test-1',
    type,
    order,
    title: null,
    audio_url: null,
    audio_script: null,
    subtitle: null,
    duration_minutes: null,
    duration_mode: 'inherit',
    passage_text: null,
    passage_subtitle: null,
    question_groups: [],
    questions: [],
    created_at: NOW,
    updated_at: NOW,
    ...overrides,
  } as unknown as Section
}

function essay(id: string, taskNumber: number, order = taskNumber): Question {
  return {
    id,
    section_id: 'w1',
    question_group_id: null,
    order,
    question_type: 'essay',
    content: {},
    answer_key: null,
    task_number: taskNumber,
    min_words: null,
    image_url: null,
    essay_type: null,
    computed_number: null,
    computed_number_end: null,
    created_at: NOW,
    updated_at: NOW,
  } as unknown as Question
}

describe('part-resolver (practice mode)', () => {
  const sections: Section[] = [
    section('l1', 'listening', 1),
    section('l2', 'listening', 2),
    section('l3', 'listening', 3),
    section('l4', 'listening', 4),
    section('r1', 'reading', 10),
    section('r2', 'reading', 11),
    section('r3', 'reading', 12),
    section('w1', 'writing', 20),
    section('s1', 'speaking', 30),
    section('s2', 'speaking', 31),
    section('s3', 'speaking', 32),
  ]

  describe('sectionsOfType', () => {
    it('returns sections sorted by order', () => {
      const listenings = sectionsOfType(sections, 'listening')
      expect(listenings.map((s) => s.id)).toEqual(['l1', 'l2', 'l3', 'l4'])
    })

    it('is stable when input is unordered', () => {
      const scrambled = [sections[3], sections[0], sections[2], sections[1]]
      expect(sectionsOfType(scrambled, 'listening').map((s) => s.id)).toEqual([
        'l1',
        'l2',
        'l3',
        'l4',
      ])
    })
  })

  describe('partCount', () => {
    it('counts sections for listening/reading/speaking', () => {
      expect(partCount(sections, 'listening')).toBe(4)
      expect(partCount(sections, 'reading')).toBe(3)
      expect(partCount(sections, 'speaking')).toBe(3)
    })

    it('counts writing tasks from questions when supplied', () => {
      expect(partCount(sections, 'writing', [essay('e1', 1), essay('e2', 2)])).toBe(2)
    })

    it('defaults writing to 2 tasks when a section exists but no essays', () => {
      expect(partCount(sections, 'writing')).toBe(2)
    })

    it('returns 0 when the skill is missing', () => {
      expect(partCount([], 'listening')).toBe(0)
    })
  })

  describe('resolvePart', () => {
    it('maps 1-based part index to the matching section', () => {
      const resolved = resolvePart(sections, 'reading', 2)
      expect(resolved).toEqual({
        sectionId: 'r2',
        writingTaskIdx: null,
        partIndex: 2,
      })
    })

    it('returns null when part index is out of range', () => {
      expect(resolvePart(sections, 'reading', 4)).toBeNull()
      expect(resolvePart(sections, 'reading', 0)).toBeNull()
    })

    it('resolves writing to the writing section with taskIdx', () => {
      const resolved = resolvePart(sections, 'writing', 2, [essay('e1', 1), essay('e2', 2)])
      expect(resolved).toEqual({
        sectionId: 'w1',
        writingTaskIdx: 1,
        partIndex: 2,
      })
    })

    it('rejects writing task index above the essay count', () => {
      expect(
        resolvePart(sections, 'writing', 3, [essay('e1', 1), essay('e2', 2)]),
      ).toBeNull()
    })
  })

  describe('partIndexForSection', () => {
    it('returns 1-based index within siblings', () => {
      expect(partIndexForSection(sections, 'l3')).toBe(3)
      expect(partIndexForSection(sections, 's1')).toBe(1)
    })

    it('returns 1 for the writing section (single row)', () => {
      expect(partIndexForSection(sections, 'w1')).toBe(1)
    })

    it('returns null for unknown ids', () => {
      expect(partIndexForSection(sections, 'nope')).toBeNull()
    })
  })

  describe('clampPart', () => {
    it('caps at the maximum part count', () => {
      expect(clampPart(sections, 'listening', 99)).toBe(4)
    })

    it('floors at 1 for zero or negative input', () => {
      expect(clampPart(sections, 'listening', 0)).toBe(1)
      expect(clampPart(sections, 'listening', -5)).toBe(1)
    })

    it('leaves in-range values unchanged', () => {
      expect(clampPart(sections, 'listening', 2)).toBe(2)
    })
  })

  describe('isSectionType', () => {
    it('accepts the four canonical types', () => {
      expect(isSectionType('listening')).toBe(true)
      expect(isSectionType('reading')).toBe(true)
      expect(isSectionType('writing')).toBe(true)
      expect(isSectionType('speaking')).toBe(true)
    })

    it('rejects everything else', () => {
      expect(isSectionType('history')).toBe(false)
      expect(isSectionType('')).toBe(false)
      expect(isSectionType('LISTENING')).toBe(false)
    })
  })

  describe('whole-section practice navigation', () => {
    // Whole-section practice scopes sortedSections to all siblings of one
    // skill — resolvePart / clampPart must still switch between those parts.
    const listeningOnly = sectionsOfType(sections, 'listening')

    it('resolves every listening part inside a scoped sibling list', () => {
      for (let part = 1; part <= 4; part++) {
        const resolved = resolvePart(listeningOnly, 'listening', part)
        expect(resolved?.sectionId).toBe(`l${part}`)
        expect(resolved?.partIndex).toBe(part)
      }
    })

    it('clamps out-of-range parts within the scoped list', () => {
      expect(clampPart(listeningOnly, 'listening', 99)).toBe(4)
      expect(clampPart(listeningOnly, 'listening', 0)).toBe(1)
    })

    it('counts parts from the scoped list only', () => {
      expect(partCount(listeningOnly, 'listening')).toBe(4)
      expect(partCount(listeningOnly, 'reading')).toBe(0)
    })
  })
})
