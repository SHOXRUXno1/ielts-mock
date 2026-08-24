import { beforeEach, describe, expect, it, vi } from 'vitest'
import { renderHook } from 'vitest-browser-react'
import { useSpeakingRecorder } from './use-speaking-recorder'

type FakeTrack = { readyState: 'live' | 'ended'; kind: string; stop: () => void }

function makeStream() {
  const track: FakeTrack = {
    readyState: 'live',
    kind: 'audio',
    stop() {
      this.readyState = 'ended'
    },
  }
  return {
    stream: {
      getTracks: () => [track],
      getAudioTracks: () => [track],
    } as unknown as MediaStream,
    track,
  }
}

/** Resolves only when the test says so, so overlapping callers can be observed. */
function deferredGetUserMedia() {
  const waiting: Array<() => void> = []
  const streams: ReturnType<typeof makeStream>[] = []
  const mock = vi.fn(
    () =>
      new Promise<MediaStream>((resolve) => {
        waiting.push(() => {
          const made = makeStream()
          streams.push(made)
          resolve(made.stream)
        })
      }),
  )
  return { mock, settleAll: () => waiting.splice(0).forEach((f) => f()), streams }
}

class FakeMediaRecorder {
  static isTypeSupported = () => true
  state: 'inactive' | 'recording' = 'inactive'
  mimeType = 'audio/webm'
  ondataavailable: ((e: { data: Blob }) => void) | null = null
  onstop: (() => void) | null = null
  constructor(public stream: MediaStream) {}
  start() {
    this.state = 'recording'
  }
  requestData() {}
  stop() {
    this.state = 'inactive'
    this.onstop?.()
  }
}

function mount(onRecordingComplete = vi.fn()) {
  return renderHook(() =>
    useSpeakingRecorder({
      turnKind: 'part1',
      onRecordingComplete,
      setPhase: vi.fn(),
    }),
  )
}

describe('useSpeakingRecorder — holding the microphone', () => {
  let gum: ReturnType<typeof deferredGetUserMedia>

  beforeEach(() => {
    gum = deferredGetUserMedia()
    vi.stubGlobal('MediaRecorder', FakeMediaRecorder)
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia: gum.mock },
    })
  })

  it('opens the device once when warm-up and a tap overlap', async () => {
    // What broke Speaking in production: the warm-up fires on a phase change and
    // the candidate taps before it has resolved. Each caller found no stream yet
    // and opened its own, leaving orphaned handles on the device; the next
    // request for an already-busy microphone fails and the turn cannot start.
    const { result } = await mount()

    const warming = result.current.warmUpMic()
    const starting = result.current.startRecording()

    expect(gum.mock).toHaveBeenCalledTimes(1)

    gum.settleAll()
    await warming
    await starting
    expect(gum.mock).toHaveBeenCalledTimes(1)
  })

  it('reuses the open device for the next answer', async () => {
    const { result } = await mount()

    const first = result.current.startRecording()
    gum.settleAll()
    await first
    result.current.stopRecording()

    const second = result.current.startRecording()
    gum.settleAll()
    await second

    expect(gum.mock).toHaveBeenCalledTimes(1)
    expect(gum.streams[0].track.readyState).toBe('live')
  })

  it('does not silence the device between answers', async () => {
    const { result } = await mount()

    const first = result.current.startRecording()
    gum.settleAll()
    await first
    result.current.stopRecording()

    expect(gum.streams[0].track.readyState).toBe('live')
  })

  it('hands the device back when the session ends', async () => {
    const { result } = await mount()

    const first = result.current.startRecording()
    gum.settleAll()
    await first
    result.current.stopRecording()
    result.current.releaseMic()

    expect(gum.streams[0].track.readyState).toBe('ended')
  })

  it('reopens a device that the machine took away', async () => {
    const { result } = await mount()

    const first = result.current.startRecording()
    gum.settleAll()
    await first
    result.current.stopRecording()

    gum.streams[0].track.readyState = 'ended'

    const second = result.current.startRecording()
    gum.settleAll()
    await second

    expect(gum.mock).toHaveBeenCalledTimes(2)
  })
})
