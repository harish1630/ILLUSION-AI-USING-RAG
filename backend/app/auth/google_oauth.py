"""Re-export Google OAuth within app.auth for consistent import paths."""

from auth.google_oauth import (
    GoogleOAuthService,
    GoogleUserInfo,
    google_oauth_service,
)

__all__ = [
    "GoogleOAuthService",
    "GoogleUserInfo",
    "google_oauth_service",
]
