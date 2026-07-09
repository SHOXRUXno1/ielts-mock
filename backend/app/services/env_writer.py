"""Utility to update a single key in the backend .env file."""

from __future__ import annotations

import re
from pathlib import Path

# Resolve .env relative to this file: backend/app/services/env_writer.py -> backend/.env
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


def update_env_key(key: str, value: str) -> None:
    """Replace or append `KEY=value` in the .env file."""
    text = _ENV_PATH.read_text(encoding="utf-8") if _ENV_PATH.exists() else ""

    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    new_line = f"{key}={value}"

    if pattern.search(text):
        text = pattern.sub(new_line, text)
    else:
        text = text.rstrip("\n") + f"\n{new_line}\n"

    _ENV_PATH.write_text(text, encoding="utf-8")
