"""Google OAuth 2.0 Client and Authentication Service for Illusion AI."""

from typing import Dict, Any, Optional
from urllib.parse import urlencode
import httpx
from pydantic import BaseModel, Field
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from app.core.config import settings
from app.core.logging import logger


class GoogleUserInfo(BaseModel):
    """Normalized Google user profile data."""
    google_id: str = Field(..., description="Google Subject identifier (sub)")
    email: str = Field(..., description="User's email address")
    name: str = Field(default="", description="Full name")
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    email_verified: bool = False
    locale: Optional[str] = None


class GoogleOAuthService:
    """Manages Google OAuth 2.0 authorization, token exchange, and verification."""

    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    DEFAULT_SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ):
        self.client_id = client_id or getattr(settings, "GOOGLE_CLIENT_ID", None) or ""
        self.client_secret = client_secret or getattr(settings, "GOOGLE_CLIENT_SECRET", None) or ""
        self.redirect_uri = redirect_uri or getattr(settings, "GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/callback")

    def get_authorization_url(
        self,
        state: Optional[str] = None,
        prompt: str = "select_account",
        access_type: str = "offline",
    ) -> str:
        """Constructs the Google OAuth 2.0 authorization URL for user consent."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.DEFAULT_SCOPES),
            "access_type": access_type,
            "prompt": prompt,
        }
        if state:
            params["state"] = state

        return f"{self.AUTH_URL}?{urlencode(params)}"

    async def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Exchanges an authorization code for Google access token and ID token."""
        target_redirect_uri = redirect_uri or self.redirect_uri

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": target_redirect_uri,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(self.TOKEN_URL, data=payload)
            if response.status_code != 200:
                logger.error(f"Google token exchange failed ({response.status_code}): {response.text}")
                raise ValueError(f"Failed to exchange Google OAuth code: {response.text}")
            return response.json()

    def verify_id_token(self, id_token_str: str) -> GoogleUserInfo:
        """Verifies a Google ID token cryptographically using google-auth library."""
        try:
            # Cryptographic validation with Google's public JWKS certificates
            request = google_requests.Request()
            payload = google_id_token.verify_oauth2_token(
                id_token_str,
                request,
                self.client_id if self.client_id else None,
            )

            return GoogleUserInfo(
                google_id=payload.get("sub", ""),
                email=payload.get("email", ""),
                name=payload.get("name", ""),
                given_name=payload.get("given_name"),
                family_name=payload.get("family_name"),
                picture=payload.get("picture"),
                email_verified=bool(payload.get("email_verified", False)),
                locale=payload.get("locale"),
            )
        except Exception as e:
            logger.error(f"Google ID token verification failed: {e}")
            raise ValueError(f"Invalid Google ID token: {str(e)}")

    async def get_user_info_from_access_token(self, access_token: str) -> GoogleUserInfo:
        """Fetches user profile directly from Google's userinfo endpoint using access token."""
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self.USERINFO_URL, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch Google userinfo ({response.status_code}): {response.text}")
                raise ValueError(f"Failed to fetch Google user info: {response.text}")

            data = response.json()
            return GoogleUserInfo(
                google_id=data.get("sub", ""),
                email=data.get("email", ""),
                name=data.get("name", ""),
                given_name=data.get("given_name"),
                family_name=data.get("family_name"),
                picture=data.get("picture"),
                email_verified=bool(data.get("email_verified", False)),
                locale=data.get("locale"),
            )


# Global singleton instance
google_oauth_service = GoogleOAuthService()
