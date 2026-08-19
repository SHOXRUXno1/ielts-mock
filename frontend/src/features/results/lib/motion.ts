export const ENTER =
  'motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2 motion-safe:fill-mode-both motion-safe:duration-300'

export function staggerStyle(index: number): { animationDelay: string } {
  return { animationDelay: `${index * 40}ms` }
}
