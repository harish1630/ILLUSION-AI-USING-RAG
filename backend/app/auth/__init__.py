"""Auth package within app namespace."""

from auth.google_oauth import (
    GoogleOAuthService,
    GoogleUserInfo,
    google_oauth_service,
)
from backend.app.auth.github_oauth import (
    GitHubOAuthService,
    GitHubUserProfile,
    github_oauth_service,
)

__all__ = [
    "GoogleOAuthService",
    "GoogleUserInfo",
    "google_oauth_service",
    "GitHubOAuthService",
    "GitHubUserProfile",
    "github_oauth_service",
]
