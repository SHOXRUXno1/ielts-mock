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
    content: { location: 'statue of Diane Gosforth' },
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
  it('keeps the map compact so question rows stay on screen', async () => {
    const screen = await render(
      <MapLabelingRenderer
        questions={[makeQuestion()]}
        options={['A', 'B', 'C']}
        imageUrl='/media/images/minster-park.png'
        answers={{}}
        onAnswer={() => {}}
      />,
    )

    const el = screen.container.querySelector('img') as HTMLImageElement
    expect(el).toBeTruthy()
    expect(el.className).toContain('max-h-[min(550px,62vh)]')
    expect(el.className).not.toContain('max-w-none')
    expect(el.className.split(/\s+/)).not.toContain('w-full')
    await expect.element(screen.getByText('statue of Diane Gosforth')).toBeVisible()
  })

  it('can hide the inline map when it is shown beside the audio', async () => {
    const screen = await render(
      <MapLabelingRenderer
        questions={[makeQuestion()]}
        options={['A', 'B', 'C']}
        imageUrl='/media/images/minster-park.png'
        answers={{}}
        onAnswer={() => {}}
        showImage={false}
      />,
    )

    await expect.element(screen.getByText('statue of Diane Gosforth')).toBeVisible()
    expect(screen.container.querySelector('img')).toBeNull()
  })
})
