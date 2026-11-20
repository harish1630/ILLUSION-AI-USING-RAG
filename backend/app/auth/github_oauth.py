"""GitHub OAuth 2.0 Client and Authentication Service for Illusion AI."""

from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
import httpx
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import logger


class GitHubUserProfile(BaseModel):
    """Normalized GitHub user profile data."""
    github_user_id: str = Field(..., description="GitHub unique user numeric ID string")
    username: str = Field(..., description="GitHub login / handle")
    email: Optional[str] = Field(default=None, description="Primary email address")
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    public_repos: int = 0
    followers: int = 0
    html_url: Optional[str] = None


class GitHubOAuthService:
    """Manages GitHub OAuth 2.0 authorization, token exchange, and API queries."""

    AUTH_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_URL = "https://api.github.com/user"
    EMAILS_URL = "https://api.github.com/user/emails"

    DEFAULT_SCOPES = ["read:user", "user:email", "repo"]

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ):
        self.client_id = client_id or getattr(settings, "GITHUB_CLIENT_ID", None) or ""
        self.client_secret = client_secret or getattr(settings, "GITHUB_CLIENT_SECRET", None) or ""
        self.redirect_uri = redirect_uri or getattr(
            settings, "GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github/callback"
        )

    def get_authorization_url(
        self,
        state: Optional[str] = None,
        scopes: Optional[List[str]] = None,
    ) -> str:
        """Constructs GitHub OAuth authorization URL for user consent."""
        scope_str = " ".join(scopes or self.DEFAULT_SCOPES)
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope_str,
        }
        if state:
            params["state"] = state
        return f"{self.AUTH_URL}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchanges authorization code for GitHub OAuth access token."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "Illusion-AI/2.0",
        }
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(self.TOKEN_URL, data=data, headers=headers)
            if resp.status_code != 200:
                logger.error(f"GitHub token exchange failed: {resp.status_code} - {resp.text}")
                raise ValueError(f"GitHub token exchange returned status {resp.status_code}")

            token_data = resp.json()
            if "error" in token_data:
                err_desc = token_data.get("error_description", token_data["error"])
                logger.error(f"GitHub token error: {err_desc}")
                raise ValueError(f"GitHub OAuth error: {err_desc}")

            return token_data

    async def get_user_profile(self, access_token: str) -> GitHubUserProfile:
        """Retrieves authenticated GitHub user's profile and primary verified email."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Illusion-AI/2.0",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(self.USER_URL, headers=headers)
            if resp.status_code != 200:
                raise ValueError(f"Failed to fetch GitHub profile: status {resp.status_code}")

            data = resp.json()
            email = data.get("email")

            # If email is private on profile, fetch from emails endpoint
            if not email:
                try:
                    email_resp = await client.get(self.EMAILS_URL, headers=headers)
                    if email_resp.status_code == 200:
                        emails = email_resp.json()
                        primary = next((e["email"] for e in emails if e.get("primary")), None)
                        email = primary or (emails[0]["email"] if emails else None)
                except Exception as e:
                    logger.warning(f"Could not fetch GitHub private emails: {e}")

            return GitHubUserProfile(
                github_user_id=str(data.get("id")),
                username=data.get("login", ""),
                email=email,
                name=data.get("name"),
                avatar_url=data.get("avatar_url"),
                bio=data.get("bio"),
                public_repos=data.get("public_repos", 0),
                followers=data.get("followers", 0),
                html_url=data.get("html_url"),
            )

    async def revoke_token(self, access_token: str) -> bool:
        """Revokes an OAuth access token via GitHub Applications API."""
        if not self.client_id or not self.client_secret:
            return False

        auth = (self.client_id, self.client_secret)
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Illusion-AI/2.0",
        }
        data = {"access_token": access_token}

        url = f"https://api.github.com/applications/{self.client_id}/grant"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.request("DELETE", url, auth=auth, json=data, headers=headers)
                return resp.status_code in (204, 200)
        except Exception as e:
            logger.warning(f"Failed to revoke GitHub token remotely: {e}")
            return False


# Global singleton instance
github_oauth_service = GitHubOAuthService()
