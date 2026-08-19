import { describe, expect, it } from 'vitest'
import { render } from 'vitest-browser-react'
import type { AttemptDetailRead } from '@/lib/api/attempts'
import { SkillRadar } from './skill-radar'

const attempt: AttemptDetailRead = {
  id: 'attempt-1',
  test_id: 'test-1',
  status: 'fully_scored',
  mode: 'full_mock',
  practice_section_id: null,
  practice_part_number: null,
  practice_section_type: null,
  practice_correct: null,
  practice_total: null,
  started_at: '2026-08-19T07:00:00.000Z',
  finished_at: '2026-08-19T10:00:00.000Z',
  overall_band: 7,
  listening_band: 7.5,
  reading_band: 7,
  writing_band: 6.5,
  speaking_band: 6,
  listening_raw: 32,
  reading_raw: 30,
  flagged_overtime: false,
  created_at: '2026-08-19T07:00:00.000Z',
  updated_at: '2026-08-19T10:00:00.000Z',
  answers: [],
  evaluation_jobs: [],
  speaking_session: null,
  test_title: 'Cambridge IELTS 15 – Test 1',
}

describe('SkillRadar', () => {
  it('renders the score-shape svg without recharts', async () => {
    const screen = await render(<SkillRadar attempt={attempt} />)
    await expect.element(screen.getByText('Score shape')).toBeInTheDocument()
    await expect.element(screen.getByLabelText('Score shape')).toBeInTheDocument()
    await expect.element(screen.getByText('Listen')).toBeInTheDocument()
    await expect.element(screen.getByText('Speak')).toBeInTheDocument()
  })
})
