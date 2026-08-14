import { createContext, useContext } from 'react'

export type ListeningAudioContextValue = {
  playingSectionId: string | null
  playingPartNumber: number | null
  position: number
  duration: number
  isPlaying: boolean
  blocked: boolean
  completed: ReadonlySet<string>
  volume: number
  allowReplay: boolean
  resume: () => void
  togglePlay: (sectionId: string) => void
  setVolume: (volume: number) => void
}

export const ListeningAudioContext =
  createContext<ListeningAudioContextValue | null>(null)

export function useListeningAudio(): ListeningAudioContextValue {
  const value = useContext(ListeningAudioContext)
  if (!value) {
    throw new Error('useListeningAudio must be used within ListeningAudioProvider')
  }
  return value
}
