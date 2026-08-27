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
}

export function parseResultSearch(search: Record<string, unknown>): ResultSearch {
  const out: ResultSearch = {}
  const tab = search.tab
  if (typeof tab === 'string' && (RESULT_TABS as readonly string[]).includes(tab)) {
    out.tab = tab as ResultTab
  }
  return out
}
