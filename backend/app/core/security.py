"""Security utilities, password hashing with Argon2id, token generation, and input sanitization."""

import re
import os
import hmac
import hashlib
import secrets
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError
    _ph = PasswordHasher(
        time_cost=3,
        memory_cost=65536,  # 64 MB
        parallelism=4,
        hash_len=32,
        salt_len=16,
    )
    _ARGON2_AVAILABLE = True
except ImportError:
    _ph = None
    _ARGON2_AVAILABLE = False


def hash_password(password: str) -> str:
    """Hashes a password using Argon2id, falling back to salted PBKDF2 if argon2 is unavailable."""
    if _ARGON2_AVAILABLE and _ph:
        return _ph.hash(password)
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"pbkdf2${salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against Argon2id or legacy PBKDF2 hashes in constant time."""
    if not hashed_password:
        return False

    # Check for Argon2id hash (starts with $argon2id$)
    if hashed_password.startswith("$argon2"):
        if _ARGON2_AVAILABLE and _ph:
            try:
                return _ph.verify(hashed_password, plain_password)
            except (VerifyMismatchError, VerificationError):
                return False
            except Exception:
                return False
        return False

    # Handle legacy salt$hash or pbkdf2$salt$hash format
    try:
        if hashed_password.startswith("pbkdf2$"):
            _, salt_hex, key_hex = hashed_password.split("$", 2)
        elif "$" in hashed_password:
            salt_hex, key_hex = hashed_password.split("$", 1)
        else:
            return False

        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        actual_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(actual_key, expected_key)
    except Exception:
        return False


def generate_reset_token() -> str:
    """Generates a cryptographically secure URL-safe password reset token."""
    return secrets.token_urlsafe(32)


def generate_oauth_state() -> str:
    """Generates a cryptographically secure URL-safe state string for OAuth flows."""
    return secrets.token_urlsafe(32)


def generate_pkce_pair() -> Tuple[str, str]:
    """Generates a high-entropy PKCE code_verifier and its base64url-encoded SHA-256 code_challenge."""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return code_verifier, code_challenge


def hash_token(token: str) -> str:
    """Returns SHA-256 hex digest of a token string for safe database lookup."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


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
