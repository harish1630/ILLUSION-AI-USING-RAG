"""Centralized Plugin Manager for Illusion AI Marketplace."""

import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import logging

from app.core.logging import logger
from app.plugins.base import BasePlugin
from app.plugins.schemas import (
    PluginToolDefinition,
    PluginCatalogItem,
    UserIntegrationResponse,
    PluginPermissionUpdate,
    PluginExecuteRequest,
    PluginExecuteResponse,
    PermissionLevel,
    ExecutionStatus,
    AuditLogItem,
    ApprovalItem,
)
from app.plugins.catalog import DEFAULT_CATALOG
from app.integrations.gmail import GmailPlugin
from app.integrations.github import GitHubPlugin

try:
    from services.token_manager import token_manager
except ImportError:
    from backend.services.token_manager import token_manager


class PluginManager:
    """Manages plugin discovery, authentication tokens, permissions, approvals, and execution."""

    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        # user_id -> plugin_id -> integration_dict (containing encrypted credentials)
        self._integrations: Dict[str, Dict[str, Dict[str, Any]]] = {}
        # user_id -> f"{plugin_id}:{tool_name}" -> PermissionLevel
        self._permissions: Dict[str, Dict[str, PermissionLevel]] = {}
        # approval_id -> dict
        self._approvals: Dict[str, Dict[str, Any]] = {}
        # List of audit log records
        self._audit_logs: List[Dict[str, Any]] = []

        # Auto-register core plugins
        self.register_plugin(GmailPlugin())
        self.register_plugin(GitHubPlugin())
        logger.info("Initialized Illusion AI Plugin Marketplace Manager with core plugins (Gmail, GitHub)")

    def register_plugin(self, plugin: BasePlugin):
        """Register a plugin instance."""
        self._plugins[plugin.plugin_id] = plugin
        logger.info(f"Registered marketplace plugin: '{plugin.plugin_id}' ({plugin.display_name})")

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """Retrieve plugin instance by ID."""
        return self._plugins.get(plugin_id)

    def list_catalog(self, user_id: str) -> List[PluginCatalogItem]:
        """List all catalog plugins annotated with the current user's connection status."""
        catalog_items = []
        user_conns = self._integrations.get(user_id, {})

        for cat in DEFAULT_CATALOG:
            p_id = cat["id"]
            plugin = self._plugins.get(p_id)
            tools = plugin.get_tools() if plugin else []
            conn = user_conns.get(p_id)

            catalog_items.append(
                PluginCatalogItem(
                    id=p_id,
                    name=cat["name"],
                    display_name=cat["display_name"],
                    description=cat["description"],
                    category=cat["category"],
                    icon=cat["icon"],
                    auth_type=cat["auth_type"],
                    scopes=cat.get("scopes", []),
                    features=cat.get("features", []),
                    is_active=cat.get("is_active", True),
                    is_connected=bool(conn and conn.get("status") == "connected"),
                    account_info={
                        "account_id": conn.get("account_id"),
                        "account_email": conn.get("account_email"),
                        "account_username": conn.get("account_username"),
                        "avatar_url": conn.get("avatar_url"),
                    } if conn else None,
                    connected_at=conn.get("connected_at") if conn else None,
                    tools=tools,
                )
            )

        return catalog_items

    def get_user_integration(self, user_id: str, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get raw integration dict (with encrypted tokens) for user."""
        return self._integrations.get(user_id, {}).get(plugin_id)

    def list_user_integrations(self, user_id: str) -> List[UserIntegrationResponse]:
        """List all active integrations for a user."""
        user_conns = self._integrations.get(user_id, {})
        responses = []

        for p_id, conn in user_conns.items():
            plugin = self._plugins.get(p_id)
            responses.append(
                UserIntegrationResponse(
                    id=conn.get("id", f"{user_id}_{p_id}"),
                    user_id=user_id,
                    plugin_id=p_id,
                    plugin_name=plugin.name if plugin else p_id,
                    plugin_display_name=plugin.display_name if plugin else p_id,
                    plugin_icon=plugin.icon if plugin else "Cpu",
                    account_id=conn.get("account_id"),
                    account_email=conn.get("account_email"),
                    account_username=conn.get("account_username"),
                    avatar_url=conn.get("avatar_url"),
                    status=conn.get("status", "connected"),
                    scopes=conn.get("scopes", []),
                    connected_at=conn.get("connected_at", datetime.now(timezone.utc).isoformat()),
                    updated_at=conn.get("updated_at", datetime.now(timezone.utc).isoformat()),
                )
            )

        return responses

    def connect_user_plugin(
        self,
        user_id: str,
        plugin_id: str,
        raw_credentials: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Encrypts tokens and stores user integration."""
        access_token = raw_credentials.get("access_token", "")
        refresh_token = raw_credentials.get("refresh_token")

        encrypted_access = token_manager.encrypt_secret(access_token)
        encrypted_refresh = token_manager.encrypt_secret(refresh_token) if refresh_token else None

        now = datetime.now(timezone.utc).isoformat()
        conn_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "plugin_id": plugin_id,
            "account_id": raw_credentials.get("account_id"),
            "account_email": raw_credentials.get("account_email"),
            "account_username": raw_credentials.get("account_username"),
            "avatar_url": raw_credentials.get("avatar_url"),
            "encrypted_access_token": encrypted_access,
            "encrypted_refresh_token": encrypted_refresh,
            "token_expires_at": raw_credentials.get("expires_at"),
            "scopes": raw_credentials.get("scopes", []),
            "status": "connected",
            "connected_at": now,
            "updated_at": now,
        }

        if user_id not in self._integrations:
            self._integrations[user_id] = {}
        self._integrations[user_id][plugin_id] = conn_data

        # Also sync to GitHubService if github plugin for backward compatibility
        if plugin_id == "github":
            github_plugin = self._plugins.get("github")
            if isinstance(github_plugin, GitHubPlugin):
                github_plugin.service.store_connection(
                    user_id=user_id,
                    github_user_id=raw_credentials.get("account_id", ""),
                    username=raw_credentials.get("account_username", "user"),
                    email=raw_credentials.get("account_email"),
                    avatar_url=raw_credentials.get("avatar_url"),
                    plaintext_token=access_token,
                )

        logger.info(f"Connected plugin '{plugin_id}' for user '{user_id}' ({conn_data.get('account_email')})")
        return conn_data

    async def disconnect_user_plugin(self, user_id: str, plugin_id: str) -> bool:
        """Disconnect and revoke a plugin integration."""
        conn = self.get_user_integration(user_id, plugin_id)
        if not conn:
            return False

        plugin = self.get_plugin(plugin_id)
        if plugin:
            try:
                # Decrypt token to revoke remotely if needed
                access_token = token_manager.decrypt_secret(conn["encrypted_access_token"])
                await plugin.revoke({"access_token": access_token})
            except Exception as e:
                logger.warning(f"Error during plugin remote revoke for {plugin_id}: {e}")

        # Remove connection
        if user_id in self._integrations:
            self._integrations[user_id].pop(plugin_id, None)

        # Clear permissions
        prefix = f"{plugin_id}:"
        user_perms = self._permissions.get(user_id, {})
        keys_to_del = [k for k in user_perms if k.startswith(prefix)]
        for k in keys_to_del:
            user_perms.pop(k, None)

        logger.info(f"Disconnected plugin '{plugin_id}' for user '{user_id}'")
        return True

    def get_permission(self, user_id: str, plugin_id: str, tool_name: str) -> PermissionLevel:
        """Evaluate permission with Default-Deny policy."""
        key = f"{plugin_id}:{tool_name}"
        # 1. Explicit user override
        user_perms = self._permissions.get(user_id, {})
        if key in user_perms:
            return user_perms[key]

        # 2. Tool-level default policy
        plugin = self.get_plugin(plugin_id)
        if plugin:
            for t in plugin.get_tools():
                if t.tool_name == tool_name:
                    return t.default_permission

        # 3. Default-Deny fallback
        return PermissionLevel.DENY

    def set_permission(self, user_id: str, plugin_id: str, tool_name: str, level: PermissionLevel):
        """Set user permission level for a tool."""
        if user_id not in self._permissions:
            self._permissions[user_id] = {}
        key = f"{plugin_id}:{tool_name}"
        self._permissions[user_id][key] = level
        logger.info(f"Updated permission for user '{user_id}' on '{key}' to {level.value}")

    def list_permissions(self, user_id: str, plugin_id: str) -> List[Dict[str, Any]]:
        """List all tool permissions for a given plugin."""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return []

        results = []
        for t in plugin.get_tools():
            current_level = self.get_permission(user_id, plugin_id, t.tool_name)
            results.append({
                "plugin_id": plugin_id,
                "tool_name": t.tool_name,
                "description": t.description,
                "is_sensitive": t.is_sensitive,
                "permission_level": current_level.value,
                "default_permission": t.default_permission.value,
            })
        return results

    def create_approval_request(
        self,
        user_id: str,
        plugin_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> str:
        """Create a pending approval request."""
        approval_id = f"appr_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        self._approvals[approval_id] = {
            "id": approval_id,
            "user_id": user_id,
            "plugin_id": plugin_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "status": "PENDING",
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=15)).isoformat(),
        }
        logger.info(f"Created approval request {approval_id} for user {user_id} on {plugin_id}:{tool_name}")
        return approval_id

    def approve_request(self, user_id: str, approval_id: str) -> bool:
        """Approve a pending request."""
        req = self._approvals.get(approval_id)
        if not req or req["user_id"] != user_id:
            return False
        req["status"] = "APPROVED"
        logger.info(f"User {user_id} APPROVED request {approval_id}")
        return True

    def reject_request(self, user_id: str, approval_id: str) -> bool:
        """Reject a pending request."""
        req = self._approvals.get(approval_id)
        if not req or req["user_id"] != user_id:
            return False
        req["status"] = "REJECTED"
        logger.info(f"User {user_id} REJECTED request {approval_id}")
        return True

    def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        return self._approvals.get(approval_id)

    async def execute_tool(
        self,
        user_id: str,
        plugin_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        approval_token: Optional[str] = None,
    ) -> PluginExecuteResponse:
        """Execute a plugin tool with permission verification and audit logging."""
        start_time = time.time()

        # Check plugin connection
        conn = self.get_user_integration(user_id, plugin_id)
        if not conn:
            duration_ms = (time.time() - start_time) * 1000
            err_msg = f"Plugin '{plugin_id}' is not connected for user '{user_id}'. Please connect via Marketplace."
            self._log_audit(user_id, plugin_id, tool_name, arguments, ExecutionStatus.DENIED, None, err_msg, duration_ms)
            return PluginExecuteResponse(
                plugin_id=plugin_id,
                tool_name=tool_name,
                status=ExecutionStatus.DENIED,
                error=err_msg,
                execution_time_ms=duration_ms,
            )

        # Check permission level
        perm = self.get_permission(user_id, plugin_id, tool_name)

        if perm == PermissionLevel.DENY:
            duration_ms = (time.time() - start_time) * 1000
            err_msg = f"Execution denied: Tool '{tool_name}' on '{plugin_id}' is blocked by policy."
            self._log_audit(user_id, plugin_id, tool_name, arguments, ExecutionStatus.DENIED, None, err_msg, duration_ms)
            return PluginExecuteResponse(
                plugin_id=plugin_id,
                tool_name=tool_name,
                status=ExecutionStatus.DENIED,
                error=err_msg,
                execution_time_ms=duration_ms,
            )

        if perm == PermissionLevel.APPROVAL_REQUIRED:
            if not approval_token:
                # Issue approval request
                appr_id = self.create_approval_request(user_id, plugin_id, tool_name, arguments)
                duration_ms = (time.time() - start_time) * 1000
                self._log_audit(user_id, plugin_id, tool_name, arguments, ExecutionStatus.APPROVAL_REQUIRED, None, "Awaiting approval", duration_ms)
                return PluginExecuteResponse(
                    plugin_id=plugin_id,
                    tool_name=tool_name,
                    status=ExecutionStatus.APPROVAL_REQUIRED,
                    approval_id=appr_id,
                    result={"message": f"Action requires user confirmation for '{tool_name}'.", "approval_id": appr_id},
                    execution_time_ms=duration_ms,
                )
            else:
                # Verify approval token
                appr = self.get_approval(approval_token)
                if not appr or appr.get("status") != "APPROVED" or appr.get("user_id") != user_id:
                    duration_ms = (time.time() - start_time) * 1000
                    err_msg = "Invalid or unapproved confirmation token provided."
                    self._log_audit(user_id, plugin_id, tool_name, arguments, ExecutionStatus.DENIED, None, err_msg, duration_ms)
                    return PluginExecuteResponse(
                        plugin_id=plugin_id,
                        tool_name=tool_name,
                        status=ExecutionStatus.DENIED,
                        error=err_msg,
                        execution_time_ms=duration_ms,
                    )

        # Decrypt credentials
        try:
            access_token = token_manager.decrypt_secret(conn["encrypted_access_token"])
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            err_msg = f"Failed to decrypt credentials for {plugin_id}: {e}"
            self._log_audit(user_id, plugin_id, tool_name, arguments, ExecutionStatus.FAILED, None, err_msg, duration_ms)
            return PluginExecuteResponse(
                plugin_id=plugin_id,
                tool_name=tool_name,
                status=ExecutionStatus.FAILED,
                error=err_msg,
                execution_time_ms=duration_ms,
            )

        plugin = self.get_plugin(plugin_id)
        if not plugin:
            duration_ms = (time.time() - start_time) * 1000
            err_msg = f"Plugin '{plugin_id}' not found in registry."
            self._log_audit(user_id, plugin_id, tool_name, arguments, ExecutionStatus.FAILED, None, err_msg, duration_ms)
            return PluginExecuteResponse(
                plugin_id=plugin_id,
                tool_name=tool_name,
                status=ExecutionStatus.FAILED,
                error=err_msg,
                execution_time_ms=duration_ms,
            )

        # Execute
        try:
            result = await plugin.execute_tool(tool_name, arguments, {"access_token": access_token})
            duration_ms = (time.time() - start_time) * 1000
            self._log_audit(user_id, plugin_id, tool_name, arguments, ExecutionStatus.SUCCESS, result, None, duration_ms)
            return PluginExecuteResponse(
                plugin_id=plugin_id,
                tool_name=tool_name,
                status=ExecutionStatus.SUCCESS,
                result=result,
                execution_time_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            err_msg = f"Plugin tool execution error: {str(e)}"
            self._log_audit(user_id, plugin_id, tool_name, arguments, ExecutionStatus.FAILED, None, err_msg, duration_ms)
            return PluginExecuteResponse(
                plugin_id=plugin_id,
                tool_name=tool_name,
                status=ExecutionStatus.FAILED,
                error=err_msg,
                execution_time_ms=duration_ms,
            )

    def _log_audit(
        self,
        user_id: str,
        plugin_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        status: ExecutionStatus,
        result: Optional[Any],
        error_message: Optional[str],
        duration_ms: float,
    ):
        """Append to audit log."""
        log_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "plugin_id": plugin_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "status": status.value,
            "result": result,
            "error_message": error_message,
            "duration_ms": duration_ms,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._audit_logs.insert(0, log_entry)
        if len(self._audit_logs) > 500:
            self._audit_logs.pop()

    def list_audit_logs(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Return user audit logs."""
        user_logs = [
            log for log in self._audit_logs
            if log["user_id"] == user_id or log["user_id"].startswith("guest_")
        ]
        if not user_logs and user_id in ("guest_user", "default_user"):
            return self._audit_logs[:limit]
        return user_logs[:limit]


# Global singleton instance
plugin_manager = PluginManager()
