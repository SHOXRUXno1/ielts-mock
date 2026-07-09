import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  __testAcquireSharedPreviewStream,
  resetSharedPreviewStreamForTests,
} from './user-camera-preview'

describe('UserCameraPreview shared stream', () => {
  beforeEach(() => {
    resetSharedPreviewStreamForTests()
    vi.restoreAllMocks()
  })

  it('dedupes in-flight getUserMedia promise', async () => {
    const getUserMedia = vi.fn(
      () =>
        new Promise<MediaStream>((resolve) => {
          setTimeout(() => {
            resolve({
              active: true,
              getTracks: () => [{ stop: vi.fn() }],
            } as unknown as MediaStream)
          }, 20)
        }),
    )

    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia },
    })

    const first = __testAcquireSharedPreviewStream()
    const second = __testAcquireSharedPreviewStream()

    await Promise.all([first, second])

    expect(getUserMedia).toHaveBeenCalledOnce()
  })
})
