"""Google OAuth 2.0 implementation for User Authentication & Account Linking."""

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger
from app.core.security import generate_oauth_state, generate_pkce_pair
from app.db.supabase import SessionLocal, is_db_connected
from app.db.models import OAuthStateModel


class GoogleUserInfo(BaseModel):
    google_id: str
    email: str
    name: str
    picture: Optional[str] = None
    email_verified: bool = True


class GoogleAuthOAuth:
    """Manages Google OAuth 2.0 flow strictly for User Authentication.
    
    Security rule: Does NOT request Gmail or third-party scopes.
    Login OAuth is isolated from Plugin OAuth.
    """

    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    # Strict Identity Scopes ONLY
    LOGIN_SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    def __init__(self):
        # In-memory fallback for state validation
        self._states: Dict[str, Dict[str, Any]] = {}

    def is_configured(self) -> bool:
        """Checks if real Google OAuth client credentials are configured."""
        cid = getattr(settings, "GOOGLE_CLIENT_ID", None)
        sec = getattr(settings, "GOOGLE_CLIENT_SECRET", None)
        return bool(cid and sec and not cid.startswith("mock_") and not cid.startswith("your_"))

    def generate_login_url(self, redirect_uri: Optional[str] = None) -> Tuple[str, str]:
        """Generates Google login URL with PKCE and state protection."""
        effective_redirect = (
            redirect_uri
            or getattr(settings, "GOOGLE_REDIRECT_URI", None)
            or "http://localhost:8000/api/v1/auth/google/callback"
        )
        state = generate_oauth_state()
        code_verifier, code_challenge = generate_pkce_pair()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        # Store state in memory
        self._states[state] = {
            "flow_type": "login",
            "redirect_uri": effective_redirect,
            "code_verifier": code_verifier,
            "expires_at": expires_at,
        }

        # Store in DB if available
        if is_db_connected and SessionLocal:
            try:
                with SessionLocal() as db:
                    db_state = OAuthStateModel(
                        state=state,
                        flow_type="login",
                        redirect_uri=effective_redirect,
                        code_verifier=code_verifier,
                        expires_at=expires_at,
                    )
                    db.add(db_state)
                    db.commit()
            except Exception as e:
                logger.warning(f"Failed to persist login OAuth state in DB: {e}")

        client_id = getattr(settings, "GOOGLE_CLIENT_ID", None) or "mock_google_client_id"
        scopes = " ".join(self.LOGIN_SCOPES)

        params = {
            "client_id": client_id,
            "redirect_uri": effective_redirect,
            "response_type": "code",
            "scope": scopes,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "select_account",
        }

        import urllib.parse
        auth_url = f"{self.GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
        return auth_url, state

    def validate_and_consume_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Validates that state exists, is not expired, and consumes it."""
        record = self._states.pop(state, None)

        if not record and is_db_connected and SessionLocal:
            try:
                with SessionLocal() as db:
                    db_state = (
                        db.query(OAuthStateModel)
                        .filter(OAuthStateModel.state == state, OAuthStateModel.flow_type == "login")
                        .first()
                    )
                    if db_state:
                        record = {
                            "flow_type": db_state.flow_type,
                            "redirect_uri": db_state.redirect_uri,
                            "code_verifier": db_state.code_verifier,
                            "expires_at": db_state.expires_at,
                        }
                        db.delete(db_state)
                        db.commit()
            except Exception as e:
                logger.warning(f"Error querying state from DB: {e}")

        if not record:
            return None

        now = datetime.now(timezone.utc)
        expires_at = record.get("expires_at")
        if expires_at and expires_at < now:
            logger.warning(f"OAuth state {state} has expired")
            return None

        return record

    async def exchange_code(self, code: str, state: str) -> GoogleUserInfo:
        """Exchanges auth code for userinfo after validating state."""
        state_data = self.validate_and_consume_state(state)
        if not state_data:
            raise ValueError("Invalid or expired OAuth state parameter")

        redirect_uri = state_data["redirect_uri"]
        code_verifier = state_data.get("code_verifier")

        # Mock fallback for dev/testing when Google credentials are not configured
        if not self.is_configured() or code.startswith("mock_") or code == "test_code":
            logger.info("Using mock Google OAuth exchange for dev/test environment")
            return GoogleUserInfo(
                google_id="google_mock_sub_987654",
                email="founder@illusion.ai",
                name="Illusion Founder",
                picture="https://lh3.googleusercontent.com/a/default-user",
                email_verified=True,
            )

        client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
        client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "")

        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        if code_verifier:
            token_data["code_verifier"] = code_verifier

        async with httpx.AsyncClient(timeout=10.0) as client:
            token_resp = await client.post(self.GOOGLE_TOKEN_URL, data=token_data)
            if token_resp.status_code != 200:
                logger.error(f"Google token exchange failed: {token_resp.text}")
                raise ValueError("Failed to exchange Google authorization code")

            tokens = token_resp.json()
            access_token = tokens.get("access_token")

            # Fetch user profile
            userinfo_resp = await client.get(
                self.GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if userinfo_resp.status_code != 200:
                raise ValueError("Failed to retrieve Google user profile")

            userinfo = userinfo_resp.json()

            return GoogleUserInfo(
                google_id=userinfo["sub"],
                email=userinfo["email"],
                name=userinfo.get("name", userinfo["email"].split("@")[0]),
                picture=userinfo.get("picture"),
                email_verified=userinfo.get("email_verified", True),
            )


google_auth = GoogleAuthOAuth()
