export const TARGET_SAMPLE_RATE = 16_000
export const PCM_CHUNK_BYTES = 6000
const YIELD_EVERY_CHUNKS = 4

export function decodeBase64Bytes(base64: string): Uint8Array {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes
}

export function floatToPcm16(samples: Float32Array): Uint8Array {
  const pcm = new Uint8Array(samples.length * 2)
  const view = new DataView(pcm.buffer)
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i] ?? 0))
    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true)
  }
  return pcm
}

export function resampleLinear(
  channelData: Float32Array,
  fromRate: number,
  toRate: number,
): Float32Array {
  if (fromRate === toRate) return channelData
  const ratio = fromRate / toRate
  const newLength = Math.max(1, Math.round(channelData.length / ratio))
  const samples = new Float32Array(newLength)
  const last = channelData.length - 1
  for (let i = 0; i < newLength; i++) {
    const src = i * ratio
    const i0 = Math.min(Math.floor(src), last)
    const i1 = Math.min(i0 + 1, last)
    const frac = src - i0
    const a = channelData[i0] ?? 0
    const b = channelData[i1] ?? 0
    samples[i] = a + (b - a) * frac
  }
  return samples
}

export async function yieldToMain(): Promise<void> {
  const sched = (
    globalThis as typeof globalThis & {
      scheduler?: { yield?: () => Promise<void> }
    }
  ).scheduler
  if (typeof sched?.yield === 'function') {
    await sched.yield()
    return
  }
  await new Promise<void>((resolve) => {
    setTimeout(resolve, 0)
  })
}

export async function forEachPcmChunk(
  pcm: Uint8Array,
  chunkBytes: number,
  send: (chunk: Uint8Array, index: number) => void,
): Promise<void> {
  let index = 0
  for (let offset = 0; offset < pcm.length; offset += chunkBytes) {
    send(pcm.subarray(offset, offset + chunkBytes), index)
    index += 1
    if (index % YIELD_EVERY_CHUNKS === 0) {
      await yieldToMain()
    }
  }
}

export async function mp3Base64ToPcm16(
  base64: string,
  audioContext: AudioContext,
): Promise<{ pcm: Uint8Array; duration: number }> {
  const bytes = decodeBase64Bytes(base64)
  if (audioContext.state === 'suspended') {
    await audioContext.resume()
  }

  const copy = new ArrayBuffer(bytes.byteLength)
  new Uint8Array(copy).set(bytes)
  const audioBuffer = await audioContext.decodeAudioData(copy)
  const duration = audioBuffer.duration

  if (typeof OfflineAudioContext === 'function') {
    const frameCount = Math.max(1, Math.ceil(duration * TARGET_SAMPLE_RATE))
    const offline = new OfflineAudioContext(1, frameCount, TARGET_SAMPLE_RATE)
    const src = offline.createBufferSource()
    src.buffer = audioBuffer
    src.connect(offline.destination)
    src.start()
    const rendered = await offline.startRendering()
    return { pcm: floatToPcm16(rendered.getChannelData(0)), duration }
  }

  return {
    pcm: floatToPcm16(
      resampleLinear(
        audioBuffer.getChannelData(0),
        audioBuffer.sampleRate,
        TARGET_SAMPLE_RATE,
      ),
    ),
    duration,
  }
}

export function iceServersKey(servers?: RTCIceServer[] | null): string {
  return servers?.length ? JSON.stringify(servers) : ''
}

/** 187.5 ms of 16 kHz PCM16 silence — Simli's documented keepalive chunk. */
export function silentPcmChunk(bytes = PCM_CHUNK_BYTES): Uint8Array {
  return new Uint8Array(bytes)
}

/**
 * getUserMedia for the candidate mic often pauses other media elements.
 * Simli's video then sits on its last frame, and the next utterance looks
 * like a still photo even though PCM is being sent. Nudge both elements
 * back into playing before we hand the avatar audio.
 */
export async function resumeSimliMedia(
  video: HTMLVideoElement | null | undefined,
  audio: HTMLAudioElement | null | undefined,
  unmuteAudio = false,
): Promise<void> {
  if (audio) {
    if (unmuteAudio) audio.volume = 1
    try {
      await audio.play()
    } catch {
      /* autoplay can still be blocked; the next user gesture will retry */
    }
  }
  if (video) {
    try {
      await video.play()
    } catch {
      /* muted video should play; ignore if the browser refuses */
    }
  }
}
