"""Token Vault: Secure encrypted storage, retrieval, and lifecycle management for OAuth provider tokens."""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from app.core.logging import logger
from app.auth.jwt import jwt_manager
from app.db.supabase import SessionLocal, is_db_connected
from app.db.models import ConnectedIntegrationModel, IntegrationTokenModel, AuditLogModel


class StoredToken(BaseModel):
    user_id: str
    plugin_id: str
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    scopes: List[str] = Field(default_factory=list)
    account_id: Optional[str] = None
    account_email: Optional[str] = None
    account_username: Optional[str] = None
    avatar_url: Optional[str] = None
    status: str = "connected"


class TokenVault:
    """Manages encrypted provider credentials (Gmail, GitHub, etc.) with per-user isolation."""

    def __init__(self):
        # In-memory resilient cache: (user_id, plugin_id) -> dict with encrypted tokens
        self._vault_cache: Dict[str, Dict[str, Any]] = {}

    def _cache_key(self, user_id: str, plugin_id: str) -> str:
        return f"{user_id}:{plugin_id.lower()}"

    def store_tokens(
        self,
        user_id: str,
        plugin_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None,
        scopes: Optional[List[str]] = None,
        account_id: Optional[str] = None,
        account_email: Optional[str] = None,
        account_username: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> bool:
        """Encrypts access and refresh tokens at rest and persists them."""
        enc_access = jwt_manager.encrypt_secret(access_token)
        enc_refresh = jwt_manager.encrypt_secret(refresh_token) if refresh_token else None

        now = datetime.now(timezone.utc)
        record = {
            "user_id": user_id,
            "plugin_id": plugin_id.lower(),
            "encrypted_access_token": enc_access,
            "encrypted_refresh_token": enc_refresh,
            "token_expires_at": token_expires_at,
            "scopes": scopes or [],
            "account_id": account_id,
            "account_email": account_email,
            "account_username": account_username,
            "avatar_url": avatar_url,
            "status": "connected",
            "updated_at": now,
        }

        # Update cache
        self._vault_cache[self._cache_key(user_id, plugin_id)] = record

        # Persist to database if connected
        if is_db_connected and SessionLocal:
            try:
                with SessionLocal() as db:
                    # Update or insert connected_integrations
                    integration = (
                        db.query(ConnectedIntegrationModel)
                        .filter(
                            ConnectedIntegrationModel.user_id == user_id,
                            ConnectedIntegrationModel.plugin_id == plugin_id.lower(),
                        )
                        .first()
                    )
                    if not integration:
                        integration = ConnectedIntegrationModel(
                            user_id=user_id,
                            plugin_id=plugin_id.lower(),
                            account_id=account_id,
                            account_email=account_email,
                            account_username=account_username,
                            avatar_url=avatar_url,
                            status="connected",
                            scopes=scopes or [],
                        )
                        db.add(integration)
                        db.flush()
                    else:
                        integration.account_id = account_id
                        integration.account_email = account_email
                        integration.account_username = account_username
                        integration.avatar_url = avatar_url
                        integration.status = "connected"
                        integration.scopes = scopes or []

                    # Update or insert integration_tokens
                    token_entry = (
                        db.query(IntegrationTokenModel)
                        .filter(
                            IntegrationTokenModel.user_id == user_id,
                            IntegrationTokenModel.plugin_id == plugin_id.lower(),
                        )
                        .first()
                    )
                    if not token_entry:
                        token_entry = IntegrationTokenModel(
                            integration_id=integration.id,
                            user_id=user_id,
                            plugin_id=plugin_id.lower(),
                            encrypted_access_token=enc_access,
                            encrypted_refresh_token=enc_refresh,
                            token_expires_at=token_expires_at,
                        )
                        db.add(token_entry)
                    else:
                        token_entry.encrypted_access_token = enc_access
                        token_entry.encrypted_refresh_token = enc_refresh
                        token_entry.token_expires_at = token_expires_at

                    # Audit log
                    audit = AuditLogModel(
                        user_id=user_id,
                        action="CONNECT_PLUGIN",
                        resource_type="plugin",
                        resource_id=plugin_id.lower(),
                        details={"account_email": account_email, "scopes": scopes},
                        status="SUCCESS",
                    )
                    db.add(audit)
                    db.commit()
            except Exception as e:
                logger.warning(f"Failed to persist tokens in DB: {e}. Cached in memory.")

        logger.info(f"TokenVault: Securely stored and encrypted tokens for user={user_id}, plugin={plugin_id}")
        return True

    def get_token(self, user_id: str, plugin_id: str) -> Optional[StoredToken]:
        """Retrieves and decrypts the access token for the given user and plugin."""
        key = self._cache_key(user_id, plugin_id)
        record = self._vault_cache.get(key)

        # Fallback to DB if not in cache
        if not record and is_db_connected and SessionLocal:
            try:
                with SessionLocal() as db:
                    integration = (
                        db.query(ConnectedIntegrationModel)
                        .filter(
                            ConnectedIntegrationModel.user_id == user_id,
                            ConnectedIntegrationModel.plugin_id == plugin_id.lower(),
                            ConnectedIntegrationModel.status == "connected",
                        )
                        .first()
                    )
                    if integration:
                        token_entry = (
                            db.query(IntegrationTokenModel)
                            .filter(
                                IntegrationTokenModel.user_id == user_id,
                                IntegrationTokenModel.plugin_id == plugin_id.lower(),
                            )
                            .first()
                        )
                        if token_entry:
                            record = {
                                "user_id": user_id,
                                "plugin_id": plugin_id.lower(),
                                "encrypted_access_token": token_entry.encrypted_access_token,
                                "encrypted_refresh_token": token_entry.encrypted_refresh_token,
                                "token_expires_at": token_entry.token_expires_at,
                                "scopes": integration.scopes or [],
                                "account_id": integration.account_id,
                                "account_email": integration.account_email,
                                "account_username": integration.account_username,
                                "avatar_url": integration.avatar_url,
                                "status": integration.status,
                            }
                            self._vault_cache[key] = record
            except Exception as e:
                logger.warning(f"Error querying tokens from DB: {e}")

        if not record or record.get("status") != "connected":
            return None

        # Decrypt tokens
        try:
            plain_access = jwt_manager.decrypt_secret(record["encrypted_access_token"])
            plain_refresh = (
                jwt_manager.decrypt_secret(record["encrypted_refresh_token"])
                if record.get("encrypted_refresh_token")
                else None
            )
            return StoredToken(
                user_id=record["user_id"],
                plugin_id=record["plugin_id"],
                access_token=plain_access,
                refresh_token=plain_refresh,
                token_expires_at=record.get("token_expires_at"),
                scopes=record.get("scopes", []),
                account_id=record.get("account_id"),
                account_email=record.get("account_email"),
                account_username=record.get("account_username"),
                avatar_url=record.get("avatar_url"),
                status=record.get("status", "connected"),
            )
        except Exception as e:
            logger.error(f"Failed to decrypt stored token for user={user_id}, plugin={plugin_id}: {e}")
            return None

    def revoke_tokens(self, user_id: str, plugin_id: str) -> bool:
        """Revokes and clears encrypted provider credentials."""
        key = self._cache_key(user_id, plugin_id)
        if key in self._vault_cache:
            self._vault_cache[key]["status"] = "revoked"
            del self._vault_cache[key]

        if is_db_connected and SessionLocal:
            try:
                with SessionLocal() as db:
                    integration = (
                        db.query(ConnectedIntegrationModel)
                        .filter(
                            ConnectedIntegrationModel.user_id == user_id,
                            ConnectedIntegrationModel.plugin_id == plugin_id.lower(),
                        )
                        .first()
                    )
                    if integration:
                        integration.status = "revoked"
                        db.query(IntegrationTokenModel).filter(
                            IntegrationTokenModel.user_id == user_id,
                            IntegrationTokenModel.plugin_id == plugin_id.lower(),
                        ).delete()

                    audit = AuditLogModel(
                        user_id=user_id,
                        action="DISCONNECT_PLUGIN",
                        resource_type="plugin",
                        resource_id=plugin_id.lower(),
                        status="SUCCESS",
                    )
                    db.add(audit)
                    db.commit()
            except Exception as e:
                logger.warning(f"Error revoking tokens in DB: {e}")

        logger.info(f"TokenVault: Revoked and purged tokens for user={user_id}, plugin={plugin_id}")
        return True

    def is_connected(self, user_id: str, plugin_id: str) -> bool:
        """Checks if user has an active, valid connection for the given plugin."""
        token = self.get_token(user_id, plugin_id)
        return token is not None and token.status == "connected"


token_vault = TokenVault()
