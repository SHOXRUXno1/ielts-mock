import { createElement, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

type Props = {
  children: ReactNode
  className?: string
}

export function InstructionBlock({ children, className }: Props) {
  return (
    <div
      className={cn(
        'rounded-lg border-l-[3px] border-blue-500 bg-slate-50 p-4 text-sm leading-[1.7] text-slate-700',
        className,
      )}
    >
      {children}
    </div>
  )
}

/**
 * Highlights sequences of 2+ consecutive UPPER CASE words (including
 * short connectors like AND, OR, A, AN, THE between them) as bold spans.
 *
 * Example: "Write ONE WORD AND/OR A NUMBER for each answer."
 *       →  "Write **ONE WORD AND/OR A NUMBER** for each answer."
 */
const SINGLE_CAPS_KEYWORDS = new Set(['TRUE', 'FALSE', 'YES', 'NO'])

/** Seeded group.instruction already lists the TFNG key — don't render it again. */
export function hasTfngKeyLegend(instruction: string): boolean {
  return /TRUE if the statement/i.test(instruction)
}

/** Seeded group.instruction already lists the YNNG key — don't render it again. */
export function hasYnngKeyLegend(instruction: string): boolean {
  return /YES if the statement/i.test(instruction)
}

export function highlightCaps(text: string): ReactNode[] {
  // Multi-word ALL-CAPS phrases, plus single IELTS keywords (TRUE/FALSE/YES/NO/…).
  const re =
    /\b([A-Z]{2,}(?:[\s/]+(?:AND|OR|A|AN|THE|[A-Z]{2,}))*(?:\/[A-Z]{2,})*)\b/g

  const parts: ReactNode[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = re.exec(text)) !== null) {
    const wordCount = match[1].split(/[\s/]+/).length
    if (wordCount < 2 && !SINGLE_CAPS_KEYWORDS.has(match[1])) continue

    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index))
    }
    parts.push(
      <span key={match.index} className='font-bold text-foreground'>
        {match[1]}
      </span>,
    )
    lastIndex = re.lastIndex
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }

  return parts.length > 0 ? parts : [text]
}

/**
 * Parses simple markdown-style bold (**text**) and italic (*text*) within
 * a single string. Returns an array of ReactNodes with <strong> and <em>.
 */
function parseInlineFormatting(text: string): ReactNode[] {
  const re = /(\*\*(.+?)\*\*|\*(.+?)\*)/g
  const parts: ReactNode[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = re.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index))
    }
    if (match[2] != null) {
      parts.push(createElement('strong', { key: match.index }, match[2]))
    } else if (match[3] != null) {
      parts.push(createElement('em', { key: match.index }, match[3]))
    }
    lastIndex = re.lastIndex
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }

  return parts.length > 0 ? parts : [text]
}

/**
 * Split passage/body text into paragraphs.
 * Official IELTS copy uses blank lines; many seeds and admin pastes use a
 * single newline. Treat any run of newlines as a break.
 */
export function splitPassageParagraphs(text: string): string[] {
  return text
    .replace(/\r\n/g, '\n')
    .split(/\n+/)
    .map((p) => p.trim())
    .filter((p) => p.length > 0)
}

/** Passage seeds use "[A]" on its own line; students see the letter only. */
export function formatPassageParagraphLabel(paragraph: string): string {
  const match = paragraph.match(/^\[([A-Z])\]$/)
  return match ? match[1] : paragraph
}

/**
 * Renders text with paragraph breaks and inline markdown (**bold**, *italic*).
 */
export function renderFormattedText(
  text: string,
  paragraphClassName = 'text-[15px] leading-[1.9] text-slate-700 tracking-[-0.01em]',
): ReactNode[] {
  const paragraphs = splitPassageParagraphs(text)
  if (paragraphs.length === 0) return []

  return paragraphs.map((para, i) =>
    createElement('p', { key: i, className: paragraphClassName },
      ...parseInlineFormatting(formatPassageParagraphLabel(para)),
    ),
  )
}
