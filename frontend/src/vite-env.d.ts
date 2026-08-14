/// <reference types="vite/client" />

/** CSS Custom Highlight API (used by passage highlighter) */
interface Highlight {
  readonly size: number
  add(range: AbstractRange): void
  clear(): void
  delete(range: AbstractRange): boolean
  has(range: AbstractRange): boolean
  values(): IterableIterator<AbstractRange>
}

declare var Highlight: {
  prototype: Highlight
  new (...initialRanges: AbstractRange[]): Highlight
}

interface HighlightRegistry {
  clear(): void
  delete(key: string): boolean
  get(key: string): Highlight | undefined
  has(key: string): boolean
  set(key: string, value: Highlight): HighlightRegistry
  keys(): IterableIterator<string>
  values(): IterableIterator<Highlight>
  entries(): IterableIterator<[string, Highlight]>
  forEach(
    callback: (value: Highlight, key: string, registry: HighlightRegistry) => void,
  ): void
  readonly size: number
}

interface CSS {
  readonly highlights: HighlightRegistry
}

interface Document {
  caretRangeFromPoint?(x: number, y: number): Range | null
}
