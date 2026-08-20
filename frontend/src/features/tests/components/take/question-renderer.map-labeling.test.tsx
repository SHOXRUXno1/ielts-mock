import { describe, expect, it, vi } from 'vitest'
import { render } from 'vitest-browser-react'
import { MapLabelingRenderer } from './question-renderer'
import type { Question } from '../../data/schema'

vi.mock('@/lib/api/attempts', () => ({
  mediaUrl: (url: string) => url,
}))

function makeQuestion(): Question {
  return {
    id: 'q15',
    section_id: 's1',
    question_group_id: 'g1',
    order: 15,
    question_type: 'map_labeling',
    content: { location: 'statue of Diana Gosforth' },
    answer_key: null,
    task_number: null,
    min_words: null,
    image_url: null,
    essay_type: null,
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
  }
}

describe('MapLabelingRenderer', () => {
  it('shows the map at full pane width so labels stay readable', async () => {
    const screen = await render(
      <MapLabelingRenderer
        questions={[makeQuestion()]}
        options={['A', 'B', 'C']}
        imageUrl='/media/images/minster-park.png'
        answers={{}}
        onAnswer={() => {}}
      />,
    )

    const img = screen.getByAltText('Map')
    await expect.element(img).toBeVisible()
    const el = img.element() as HTMLImageElement
    expect(el.className).toContain('w-full')
    expect(el.className).not.toContain('max-w-lg')
  })
})
