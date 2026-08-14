type FullscreenElement = HTMLElement & {
  webkitRequestFullscreen?: () => Promise<void>
}

/** Enter browser fullscreen (F11-like). Must run from a user click. */
export function enterExamFullscreen(): void {
  const el = document.documentElement as FullscreenElement
  const already =
    document.fullscreenElement ??
    (document as Document & { webkitFullscreenElement?: Element })
      .webkitFullscreenElement
  if (already) return

  const req = el.requestFullscreen?.bind(el) ?? el.webkitRequestFullscreen?.bind(el)
  if (!req) return
  void Promise.resolve(req()).catch(() => {
    // Denied or unsupported (iOS, iframe, etc.) — exam still starts.
  })
}
