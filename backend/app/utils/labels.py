"""Display-label helpers for denormalized API fields."""

import re

_TEST_SUFFIX = re.compile(r"(?i)\bTest\s+\d+\s*$")


def format_test_label(title: str, test_number: int | None) -> str:
    """Display label that disambiguates tests from the same book.

    Appends the test number so short titles like "Ielts 18" become
    "Ielts 18 — Test 1". Skips appending when the title already ends
    with "Test N" (e.g. seeded "Cambridge IELTS 9 – Test 4").
    """
    label = (title or "").strip()
    if _TEST_SUFFIX.search(label):
        return label
    return f"{label} — Test {test_number or 1}"
