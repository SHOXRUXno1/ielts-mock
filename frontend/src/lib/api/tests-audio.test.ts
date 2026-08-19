import { describe, expect, it } from 'vitest'
import { assertAudioUpload, MAX_AUDIO_UPLOAD_BYTES } from './tests'

describe('assertAudioUpload', () => {
  it('accepts an mp3 even when the browser sends octet-stream', () => {
    const file = new File([new Uint8Array([1, 2, 3])], 'part1.mp3', {
      type: 'application/octet-stream',
    })
    expect(() => assertAudioUpload(file)).not.toThrow()
  })

  it('rejects an empty file and a non-audio name', () => {
    expect(() =>
      assertAudioUpload(new File([], 'part1.mp3', { type: 'audio/mpeg' })),
    ).toThrow(/empty/i)
    expect(() =>
      assertAudioUpload(new File([new Uint8Array([1])], 'notes.txt', { type: 'text/plain' })),
    ).toThrow(/unsupported/i)
  })

  it('rejects files over the server cap', () => {
    const oversized = new File([new Uint8Array(8)], 'part1.mp3', {
      type: 'audio/mpeg',
    })
    Object.defineProperty(oversized, 'size', { value: MAX_AUDIO_UPLOAD_BYTES + 1 })
    expect(() => assertAudioUpload(oversized)).toThrow(/too large/i)
  })
})
