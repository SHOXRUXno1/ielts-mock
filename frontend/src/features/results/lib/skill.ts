import { BookOpen, Headphones, Mic, PenLine, type LucideIcon } from 'lucide-react'

export const SKILL_KEYS = ['listening', 'reading', 'writing', 'speaking'] as const

export type SkillKey = (typeof SKILL_KEYS)[number]

export type SkillMeta = {
  key: SkillKey
  label: string
  icon: LucideIcon
  accent: string
  surface: string
  bar: string
  ring: string
}

export const SKILL_META: Record<SkillKey, SkillMeta> = {
  listening: {
    key: 'listening',
    label: 'Listening',
    icon: Headphones,
    accent: 'text-skill-listening',
    surface: 'bg-skill-listening-soft',
    bar: 'bg-skill-listening',
    ring: 'stroke-skill-listening',
  },
  reading: {
    key: 'reading',
    label: 'Reading',
    icon: BookOpen,
    accent: 'text-skill-reading',
    surface: 'bg-skill-reading-soft',
    bar: 'bg-skill-reading',
    ring: 'stroke-skill-reading',
  },
  writing: {
    key: 'writing',
    label: 'Writing',
    icon: PenLine,
    accent: 'text-skill-writing',
    surface: 'bg-skill-writing-soft',
    bar: 'bg-skill-writing',
    ring: 'stroke-skill-writing',
  },
  speaking: {
    key: 'speaking',
    label: 'Speaking',
    icon: Mic,
    accent: 'text-skill-speaking',
    surface: 'bg-skill-speaking-soft',
    bar: 'bg-skill-speaking',
    ring: 'stroke-skill-speaking',
  },
}

export function skillMeta(key: string): SkillMeta {
  if (key in SKILL_META) return SKILL_META[key as SkillKey]
  return SKILL_META.listening
}
