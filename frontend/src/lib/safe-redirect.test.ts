import { describe, expect, it } from 'vitest'
import { parseSafeRedirect } from './safe-redirect'

describe('parseSafeRedirect', () => {
  it('keeps in-app paths with search and hash', () => {
    expect(parseSafeRedirect('/student/profile')).toBe('/student/profile')
    expect(parseSafeRedirect('/student/results?tab=writing')).toBe(
      '/student/results?tab=writing',
    )
    expect(parseSafeRedirect('/tests/1#part')).toBe('/tests/1#part')
  })

  it('rejects protocol-relative and empty values', () => {
    expect(parseSafeRedirect('//evil.example/phish')).toBeUndefined()
    expect(parseSafeRedirect('')).toBeUndefined()
    expect(parseSafeRedirect('   ')).toBeUndefined()
    expect(parseSafeRedirect(undefined)).toBeUndefined()
    expect(parseSafeRedirect(1)).toBeUndefined()
  })

  it('rejects login itself so the next hop cannot loop', () => {
    expect(parseSafeRedirect('/login')).toBeUndefined()
    expect(parseSafeRedirect('/login?redirect=/student/dashboard')).toBeUndefined()
  })

  it('accepts same-origin absolute URLs and strips the origin', () => {
    const href = `${window.location.origin}/student/dashboard?x=1`
    expect(parseSafeRedirect(href)).toBe('/student/dashboard?x=1')
  })

  it('rejects other origins and non-path schemes', () => {
    expect(parseSafeRedirect('https://evil.example/student')).toBeUndefined()
    expect(parseSafeRedirect('javascript:alert(1)')).toBeUndefined()
  })
})
