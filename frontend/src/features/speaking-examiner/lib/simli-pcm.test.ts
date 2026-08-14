import { describe, expect, it } from 'vitest'
import {
  floatToPcm16,
  forEachPcmChunk,
  iceServersKey,
  PCM_CHUNK_BYTES,
  resampleLinear,
} from './simli-pcm'

describe('simli-pcm', () => {
  it('encodes clamped PCM16 little-endian', () => {
    const pcm = floatToPcm16(new Float32Array([0, 1, -1, 2, -2]))
    const view = new DataView(pcm.buffer)
    expect(view.getInt16(0, true)).toBe(0)
    expect(view.getInt16(2, true)).toBe(0x7fff)
    expect(view.getInt16(4, true)).toBe(-0x8000)
    expect(view.getInt16(6, true)).toBe(0x7fff)
    expect(view.getInt16(8, true)).toBe(-0x8000)
  })

  it('resamples with linear interpolation', () => {
    const src = new Float32Array([0, 1])
    const out = resampleLinear(src, 2, 4)
    expect(out).toHaveLength(4)
    expect(out[0]).toBeCloseTo(0)
    expect(out[1]).toBeCloseTo(0.5)
    expect(out[3]).toBeCloseTo(1)
  })

  it('sends every PCM chunk', async () => {
    const pcm = new Uint8Array(PCM_CHUNK_BYTES * 5)
    const lengths: number[] = []
    await forEachPcmChunk(pcm, PCM_CHUNK_BYTES, (chunk) => {
      lengths.push(chunk.length)
    })
    expect(lengths).toEqual([
      PCM_CHUNK_BYTES,
      PCM_CHUNK_BYTES,
      PCM_CHUNK_BYTES,
      PCM_CHUNK_BYTES,
      PCM_CHUNK_BYTES,
    ])
  })

  it('treats identical ICE servers as the same key', () => {
    const servers = [{ urls: 'stun:stun.l.google.com:19302' }]
    expect(iceServersKey(servers)).toBe(iceServersKey([...servers]))
    expect(iceServersKey(null)).toBe('')
  })
})
