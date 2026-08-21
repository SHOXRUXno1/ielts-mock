export const RESULT_TABS = [
  'overview',
  'listening',
  'reading',
  'writing',
  'speaking',
] as const

export type ResultTab = (typeof RESULT_TABS)[number]

export type ResultSearch = {
  tab?: ResultTab
  reveal?: boolean
}

export function parseResultSearch(search: Record<string, unknown>): ResultSearch {
  const out: ResultSearch = {}
  const tab = search.tab
  if (typeof tab === 'string' && (RESULT_TABS as readonly string[]).includes(tab)) {
    out.tab = tab as ResultTab
  }
  const reveal = search.reveal
  if (reveal === true || reveal === 1 || reveal === '1' || reveal === 'true') {
    out.reveal = true
  }
  return out
}
