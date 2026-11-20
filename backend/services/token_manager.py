"""JWT Token Manager for Illusion AI session management and authentication."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Set
import jwt
from pydantic import BaseModel, Field
from cryptography.fernet import Fernet

from app.core.config import settings
from app.core.logging import logger


class TokenPair(BaseModel):
    """Access and refresh token bundle returned upon successful login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiry lifetime in seconds")


class TokenPayload(BaseModel):
    """Decoded token payload structure."""
    sub: str = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email")
    token_type: str = Field(..., description="'access' or 'refresh'")
    jti: str = Field(..., description="Unique token ID")
    exp: int
    iat: int
    name: Optional[str] = None
    picture: Optional[str] = None
    roles: list[str] = Field(default_factory=lambda: ["user"])


class TokenManager:
    """Handles JWT generation, cryptographic verification, revocation, and refresh cycles."""

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: Optional[str] = None,
        access_token_expire_minutes: Optional[int] = None,
        refresh_token_expire_days: Optional[int] = None,
    ):
        self.secret_key = (
            secret_key
            or getattr(settings, "JWT_SECRET_KEY", None)
            or "illusion_ai_super_secret_jwt_key_2026_change_in_production"
        )
        self.algorithm = algorithm or getattr(settings, "JWT_ALGORITHM", "HS256")
        self.access_expire_minutes = access_token_expire_minutes or getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60)
        self.refresh_expire_days = refresh_token_expire_days or getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 7)

        # Fernet symmetric encryption setup
        encryption_key = getattr(settings, "TOKEN_ENCRYPTION_KEY", None)
        self._fernet: Optional[Fernet] = None
        if encryption_key and len(encryption_key.strip()) > 10:
            try:
                self._fernet = Fernet(encryption_key.strip().encode())
            except Exception as e:
                logger.warning(f"Invalid Fernet encryption key format: {e}")

        # In-memory revocation blacklist (can be backed by Redis / Supabase in production)
        self._revoked_tokens: Set[str] = set()

    def encrypt_secret(self, plaintext: str) -> str:
        """Encrypts sensitive plaintext (such as Google refresh tokens) using Fernet."""
        if not self._fernet:
            return plaintext
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt_secret(self, ciphertext: str) -> str:
        """Decrypts Fernet ciphertext back to plaintext."""
        if not self._fernet:
            return ciphertext
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            logger.error(f"Fernet decryption failed: {e}")
            raise ValueError("Failed to decrypt secret payload")

    def create_access_token(
        self,
        user_id: str,
        email: str,
        name: Optional[str] = None,
        picture: Optional[str] = None,
        roles: Optional[list[str]] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Generates a signed JWT access token for API requests."""
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(minutes=self.access_expire_minutes))

        payload = {
            "sub": str(user_id),
            "email": email,
            "name": name or "",
            "picture": picture,
            "roles": roles or ["user"],
            "token_type": "access",
            "jti": str(uuid.uuid4()),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        user_id: str,
        email: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Generates a long-lived JWT refresh token."""
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(days=self.refresh_expire_days))

        payload = {
            "sub": str(user_id),
            "email": email,
            "token_type": "refresh",
            "jti": str(uuid.uuid4()),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_token_pair(
        self,
        user_id: str,
        email: str,
        name: Optional[str] = None,
        picture: Optional[str] = None,
        roles: Optional[list[str]] = None,
    ) -> TokenPair:
        """Generates both an access token and a refresh token."""
        access_token = self.create_access_token(
            user_id=user_id,
            email=email,
            name=name,
            picture=picture,
            roles=roles,
        )
        refresh_token = self.create_refresh_token(
            user_id=user_id,
            email=email,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_expire_minutes * 60,
        )

    def decode_token(self, token: str, verify_exp: bool = True) -> Dict[str, Any]:
        """Decodes and validates token signature and expiry."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": verify_exp},
            )

            # Check blacklist
            jti = payload.get("jti")
            if jti and jti in self._revoked_tokens:
                raise ValueError("Token has been revoked")

            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    def verify_token(self, token: str, expected_type: str = "access") -> Optional[TokenPayload]:
        """Validates token and returns typed TokenPayload if valid."""
        try:
            payload_dict = self.decode_token(token)
            actual_type = payload_dict.get("token_type")

            if actual_type != expected_type:
                logger.warning(f"Token type mismatch: expected {expected_type}, got {actual_type}")
                return None

            return TokenPayload(**payload_dict)
        except Exception as e:
            logger.debug(f"Token verification failed: {e}")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[TokenPair]:
        """Generates a new token pair from a valid refresh token."""
        payload = self.verify_token(refresh_token, expected_type="refresh")
        if not payload:
            return None

        # Revoke old refresh token to prevent replay attacks (token rotation)
        self.revoke_token(refresh_token)

        # Issue fresh token pair
        return self.create_token_pair(
            user_id=payload.sub,
            email=payload.email,
            name=payload.name,
            picture=payload.picture,
            roles=payload.roles,
        )

    def revoke_token(self, token: str) -> bool:
        """Adds token jti to revoked blacklist."""
        try:
            payload = self.decode_token(token, verify_exp=False)
            jti = payload.get("jti")
            if jti:
                self._revoked_tokens.add(jti)
                logger.info(f"Revoked token with JTI: {jti}")
                return True
        except Exception as e:
            logger.warning(f"Failed to revoke token: {e}")
        return False

    def is_revoked(self, jti: str) -> bool:
        """Checks if token JTI is in revocation set."""
        return jti in self._revoked_tokens


# Global singleton instance
token_manager = TokenManager()
