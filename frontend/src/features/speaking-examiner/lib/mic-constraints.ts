/**
 * getUserMedia audio constraints for the Speaking examiner.
 *
 * Kept in one place because two callers open the microphone — the pre-flight
 * mic check and the recorder itself — and their settings must not drift. What
 * one applies at check time is what the other must record with, or a candidate
 * whose voice tested fine can still be recorded through a different filter
 * chain.
 *
 * The four DSP toggles map to the failure modes we see on cheap headsets:
 *   - echoCancellation strips the examiner's own voice leaking back through
 *     the mic when the candidate has the speakers on instead of headphones.
 *   - noiseSuppression is the browser's built-in denoiser for the constant
 *     hiss / mains hum a cheap capsule adds under everything.
 *   - autoGainControl levels a candidate who drifts between whispering and
 *     shouting into the mic, so Whisper is not fed a signal that swings
 *     between clipping and near-silence inside one answer.
 *   - channelCount: 1 asks the device for mono. Stereo from a mono capsule
 *     is duplicated bytes, and every STT engine here downmixes anyway.
 *
 * sampleRate is a hint the browser is allowed to ignore; Whisper / Chirp
 * both work in 16 kHz internally, so asking gives them their native rate
 * when the driver honours it and costs nothing when it does not.
 */
export const SPEAKING_AUDIO_CONSTRAINTS: MediaStreamConstraints = {
  audio: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
    channelCount: 1,
    sampleRate: 16000,
  },
}
