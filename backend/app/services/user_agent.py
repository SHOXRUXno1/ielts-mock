"""Lightweight user-agent parser (no external dependency)."""

from __future__ import annotations

import re

_BROWSER_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Edge", re.compile(r"Edg(?:e|A|iOS)?/(\d+(?:\.\d+)?)", re.I)),
    ("Opera", re.compile(r"(?:OPR|Opera)/(\d+(?:\.\d+)?)", re.I)),
    ("Chrome", re.compile(r"Chrome/(\d+(?:\.\d+)?)", re.I)),
    ("Firefox", re.compile(r"Firefox/(\d+(?:\.\d+)?)", re.I)),
    ("Safari", re.compile(r"Version/(\d+(?:\.\d+)?).*Safari/", re.I)),
]

_OS_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Windows", re.compile(r"Windows NT", re.I)),
    # iOS UAs also contain "Mac OS X" — check iPhone/iPad before macOS
    ("iOS", re.compile(r"(?:iPhone|iPad|iPod)", re.I)),
    ("macOS", re.compile(r"Mac OS X", re.I)),
    ("Android", re.compile(r"Android", re.I)),
    ("Linux", re.compile(r"Linux", re.I)),
]


def parse_user_agent(ua: str | None) -> tuple[str, str, str]:
    """Return (device_type, browser, os_name).

    Examples: ('desktop', 'Chrome 138', 'Windows')
    """
    text = (ua or "").strip()
    if not text:
        return "unknown", "Unknown", "Unknown"

    browser = "Unknown"
    for name, pattern in _BROWSER_PATTERNS:
        match = pattern.search(text)
        if match:
            # Chrome pattern also matches Edge/Opera — skip if already matched earlier
            if name == "Chrome" and re.search(r"Edg(?:e|A|iOS)?/|OPR/", text, re.I):
                continue
            if name == "Safari" and re.search(r"Chrome/|Chromium/", text, re.I):
                continue
            version = match.group(1).split(".")[0]
            browser = f"{name} {version}"
            break

    os_name = "Unknown"
    for name, pattern in _OS_PATTERNS:
        if pattern.search(text):
            os_name = name
            break

    lower = text.lower()
    if "ipad" in lower or ("android" in lower and "mobile" not in lower):
        device_type = "tablet"
    elif any(
        token in lower
        for token in ("mobile", "iphone", "ipod", "android", "iemobile")
    ):
        device_type = "mobile"
    elif os_name != "Unknown":
        device_type = "desktop"
    else:
        device_type = "unknown"

    return device_type, browser, os_name
