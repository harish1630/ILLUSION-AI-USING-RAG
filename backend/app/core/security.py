"""Security utilities, password hashing, token generation, and input sanitization."""

import re
import os
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional


def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a unique cryptographic salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored salt$hash in constant time."""
    if not hashed_password or "$" not in hashed_password:
        return False
    try:
        salt_hex, key_hex = hashed_password.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        actual_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(actual_key, expected_key)
    except Exception:
        return False


def generate_reset_token() -> str:
    """Generates a cryptographically secure URL-safe password reset token."""
    return secrets.token_urlsafe(32)


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
