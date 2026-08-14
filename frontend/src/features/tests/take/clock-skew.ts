/**
 * Clock skew from an explicit server_now ISO timestamp in a JSON body.
 * Returns serverNow - clientNow (positive when server is ahead).
 * Used with SectionProgress.server_now — not Date headers / client deadlines.
 */
export function skewFromServerNow(serverNow: string | null | undefined): number {
  if (!serverNow) return 0
  const server = Date.parse(serverNow)
  if (Number.isNaN(server)) return 0
  return server - Date.now()
}
