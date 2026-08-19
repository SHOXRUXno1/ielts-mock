import { describe, expect, it } from 'vitest'
import { bandDescriptor, cefrLevel } from './cefr'

describe('bandDescriptor', () => {
  it('returns null for empty bands', () => {
    expect(bandDescriptor(null)).toBeNull()
    expect(bandDescriptor(undefined)).toBeNull()
  })

  it('maps IELTS bands to descriptors', () => {
    expect(bandDescriptor(9)).toBe('Expert')
    expect(bandDescriptor(8)).toBe('Very good')
    expect(bandDescriptor(7)).toBe('Good')
    expect(bandDescriptor(6)).toBe('Competent')
    expect(bandDescriptor(5)).toBe('Modest')
    expect(bandDescriptor(4)).toBe('Limited')
    expect(bandDescriptor(3.5)).toBe('Limited')
  })
})

describe('cefrLevel', () => {
  it('returns null for empty bands', () => {
    expect(cefrLevel(null)).toBeNull()
  })

  it('maps IELTS bands to CEFR levels', () => {
    expect(cefrLevel(8.5)).toBe('C2')
    expect(cefrLevel(7)).toBe('C1')
    expect(cefrLevel(5.5)).toBe('B2')
    expect(cefrLevel(4)).toBe('B1')
    expect(cefrLevel(3.5)).toBe('A2')
  })
})
