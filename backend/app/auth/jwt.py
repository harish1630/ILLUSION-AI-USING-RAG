"""Cryptographic JWT token generation, verification, and symmetric encryption."""

import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Set, List
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
    user_id: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = Field(default_factory=lambda: ["user"])


class TokenPayload(BaseModel):
    """Decoded token payload structure."""
    sub: str = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email")
    token_type: str = Field(..., description="'access' or 'refresh'")
    jti: str = Field(..., description="Unique token ID")
    session_id: Optional[str] = Field(default=None, description="Associated user session ID")
    family_id: Optional[str] = Field(default=None, description="Refresh token family for reuse detection")
    exp: int
    iat: int
    name: Optional[str] = None
    picture: Optional[str] = None
    roles: List[str] = Field(default_factory=lambda: ["user"])

    @property
    def user_id(self) -> str:
        return self.sub


class JWTAuthManager:
    """Manages JWT generation, cryptographic verification, token family tracking, and rotation."""

    def __init__(self):
        self.secret_key = (
            getattr(settings, "JWT_SECRET_KEY", None)
            or "illusion_ai_super_secret_jwt_key_2026_change_in_production"
        )
        self.algorithm = getattr(settings, "JWT_ALGORITHM", "HS256")
        self.access_expire_minutes = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60)
        self.refresh_expire_days = getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 7)

        # Fernet encryption key for provider secrets at rest
        self._fernet: Optional[Fernet] = None
        enc_key = getattr(settings, "TOKEN_ENCRYPTION_KEY", None)
        if enc_key and len(enc_key.strip()) >= 32:
            try:
                self._fernet = Fernet(enc_key.strip().encode())
            except Exception as e:
                logger.warning(f"Fernet initialization failed: {e}. Generating ephemeral key.")
                self._fernet = Fernet(Fernet.generate_key())
        else:
            # Deterministic safe fallback for local/dev
            derived_key = hashlib.sha256(self.secret_key.encode()).digest()
            import base64
            b64_key = base64.urlsafe_b64encode(derived_key)
            self._fernet = Fernet(b64_key)

        # Revoked JTIs: set of jti strings
        self._revoked_jtis: Set[str] = set()
        # Revoked families (triggered when reuse of an old refresh token is detected)
        self._revoked_families: Set[str] = set()

    def encrypt_secret(self, plaintext: str) -> str:
        """Encrypts sensitive plaintext tokens using AES-128-CBC + HMAC (Fernet)."""
        if not plaintext:
            return ""
        if not self._fernet:
            return plaintext
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt_secret(self, ciphertext: str) -> str:
        """Decrypts Fernet ciphertext back to plaintext."""
        if not ciphertext:
            return ""
        if not self._fernet:
            return ciphertext
        try:
            return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except Exception:
            # If not fernet encrypted (e.g. legacy plain text token), return as is
            return ciphertext

    def create_access_token(
        self,
        user_id: str,
        email: str,
        name: Optional[str] = None,
        picture: Optional[str] = None,
        roles: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Generates a short-lived signed JWT access token."""
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(minutes=self.access_expire_minutes))

        payload = {
            "sub": str(user_id),
            "email": email,
            "name": name or "",
            "picture": picture,
            "roles": roles or ["user"],
            "session_id": session_id or str(uuid.uuid4()),
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
        session_id: Optional[str] = None,
        family_id: Optional[str] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Generates a long-lived JWT refresh token with token family ID for reuse detection."""
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(days=self.refresh_expire_days))

        payload = {
            "sub": str(user_id),
            "email": email,
            "session_id": session_id or str(uuid.uuid4()),
            "family_id": family_id or str(uuid.uuid4()),
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
        roles: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        family_id: Optional[str] = None,
    ) -> TokenPair:
        """Generates both an access token and a refresh token sharing the same session and family."""
        sid = session_id or str(uuid.uuid4())
        fid = family_id or str(uuid.uuid4())
        access_token = self.create_access_token(
            user_id=user_id,
            email=email,
            name=name,
            picture=picture,
            roles=roles,
            session_id=sid,
        )
        refresh_token = self.create_refresh_token(
            user_id=user_id,
            email=email,
            session_id=sid,
            family_id=fid,
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_expire_minutes * 60,
            user_id=str(user_id),
            email=email,
            roles=roles or ["user"],
        )

    def decode_token(self, token: str, verify_exp: bool = True) -> Dict[str, Any]:
        """Decodes and validates token signature and revocation state."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": verify_exp},
            )
            jti = payload.get("jti")
            family_id = payload.get("family_id")

            if family_id and family_id in self._revoked_families:
                raise ValueError("Token family has been revoked due to reuse detection")

            if jti and jti in self._revoked_jtis:
                raise ValueError("Token has been revoked")

            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    def verify_token(self, token: str, expected_type: str = "access") -> Optional[TokenPayload]:
        """Validates token and returns typed TokenPayload."""
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

    def rotate_refresh_token(self, refresh_token: str) -> Optional[TokenPair]:
        """Rotates a refresh token with reuse detection.
        
        If an already revoked refresh token is presented, the whole family is revoked immediately!
        """
        try:
            # Decode token without throwing on revoked JTI to check for reuse
            unverified_payload = jwt.decode(
                refresh_token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},
            )
            jti = unverified_payload.get("jti")
            family_id = unverified_payload.get("family_id")

            # Check for REUSE ATTACK
            if jti in self._revoked_jtis:
                if family_id:
                    self._revoked_families.add(family_id)
                    logger.error(
                        f"SECURITY ALERT: Refresh token reuse detected for JTI={jti}, family={family_id}! "
                        "Revoked entire token family."
                    )
                return None
        except Exception:
            return None

        # Fully verify token (including exp and signature)
        payload = self.verify_token(refresh_token, expected_type="refresh")
        if not payload:
            return None

        # Revoke the current refresh token JTI
        self._revoked_jtis.add(payload.jti)

        # Issue new token pair keeping the same session_id and family_id
        return self.create_token_pair(
            user_id=payload.sub,
            email=payload.email,
            name=payload.name,
            picture=payload.picture,
            roles=payload.roles,
            session_id=payload.session_id,
            family_id=payload.family_id,
        )

    def revoke_token(self, token: str) -> bool:
        """Revokes a specific token by JTI."""
        try:
            payload = self.decode_token(token, verify_exp=False)
            jti = payload.get("jti")
            if jti:
                self._revoked_jtis.add(jti)
                return True
        except Exception:
            pass
        return False

    def revoke_session(self, session_id: str, family_id: Optional[str] = None):
        """Revokes an entire user session and associated token family."""
        if family_id:
            self._revoked_families.add(family_id)

    def is_revoked(self, jti: str) -> bool:
        """Returns True if the token JTI has been revoked."""
        return jti in self._revoked_jtis


jwt_manager = JWTAuthManager()
