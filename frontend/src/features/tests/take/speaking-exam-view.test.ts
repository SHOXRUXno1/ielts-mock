import { describe, expect, it } from 'vitest'
import { resolveSpeakingExamView } from './speaking-exam-view'

describe('resolveSpeakingExamView', () => {
  it('keeps preview and practice on the session', () => {
    expect(
      resolveSpeakingExamView({
        isLiveExam: false,
        progressLoaded: false,
        speakingState: null,
      }),
    ).toBe('session')
  })

  it('waits for progress before mounting the examiner', () => {
    expect(
      resolveSpeakingExamView({
        isLiveExam: true,
        progressLoaded: false,
        speakingState: null,
      }),
    ).toBe('loading')
  })

  it('shows the readiness gate until Speaking is entered', () => {
    expect(
      resolveSpeakingExamView({
        isLiveExam: true,
        progressLoaded: true,
        speakingState: 'not_started',
      }),
    ).toBe('gate')
  })

  it('mounts the examiner once Speaking is active', () => {
    expect(
      resolveSpeakingExamView({
        isLiveExam: true,
        progressLoaded: true,
        speakingState: 'active',
      }),
    ).toBe('session')
  })
})
