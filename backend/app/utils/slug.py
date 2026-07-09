import re


def generate_book_slug(title: str) -> str:
    """Convert a book title to a URL-safe slug.

    Examples:
        "Cambridge IELTS 1"      → "cambridge-ielts-1"
        "IELTS OG Academic 2014" → "ielts-og-academic-2014"
    """
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")
