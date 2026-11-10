"""Security utilities, input sanitization, and authorization helpers."""

import re
from typing import Optional


def sanitize_input_text(text: str, max_length: int = 4000) -> str:
    """Sanitizes user input text without corrupting Unicode/Tamil characters."""
    if not text:
        return ""
    # Strip dangerous control characters but preserve tabs, newlines, and full Unicode
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    return cleaned.strip()[:max_length]


def sanitize_filename(filename: str) -> str:
    """Sanitizes uploaded filename against directory traversal attacks."""
    clean = re.sub(r"[^a-zA-Z0-9_.\-\u0B80-\u0BFF]", "_", filename)
    clean = clean.lstrip(".")
    return clean or "document.pdf"

