"""FastAPI routes for Illusion AI Plugin Marketplace."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import logger
from app.routes.auth import get_current_user_optional, CurrentUser
from app.plugins import (
    plugin_manager,
    PluginCatalogItem,
    UserIntegrationResponse,
    PluginPermissionUpdate,
    PluginExecuteRequest,
    PluginExecuteResponse,
    OAuthConnectResponse,
    AuditLogItem,
    PermissionLevel,
)

router = APIRouter(prefix="/api/marketplace", tags=["Plugin Marketplace"])


def resolve_user_id(current_user: Optional[CurrentUser]) -> str:
    """Helper to extract user ID or provide safe fallback."""
    if current_user and current_user.sub:
        return current_user.sub
    return "guest_user"


# ---------------------------------------------------------------------------
# 1. Catalog & Active Integrations
# ---------------------------------------------------------------------------

@router.get("/plugins", response_model=List[PluginCatalogItem])
async def list_plugins(current_user: Optional[CurrentUser] = Depends(get_current_user_optional)):
    """List all available marketplace plugins with connection status for the current user."""
    user_id = resolve_user_id(current_user)
    return plugin_manager.list_catalog(user_id)


@router.get("/integrations", response_model=List[UserIntegrationResponse])
async def list_user_integrations(current_user: Optional[CurrentUser] = Depends(get_current_user_optional)):
    """List all active connected integrations for the current user."""
    user_id = resolve_user_id(current_user)
    return plugin_manager.list_user_integrations(user_id)


# ---------------------------------------------------------------------------
# 2. OAuth Connection Flow
# ---------------------------------------------------------------------------

@router.post("/connect/{plugin_id}", response_model=OAuthConnectResponse)
async def connect_plugin(
    plugin_id: str,
    redirect_uri: Optional[str] = Query(None, description="Frontend or backend callback URI"),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Generate OAuth authorization URL to connect an external application."""
    user_id = resolve_user_id(current_user)
    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found in catalog")

    callback_url = redirect_uri or f"{settings.FRONTEND_URL}/marketplace?callback=true&plugin_id={plugin_id}"
    # Standard backend callback
    backend_callback = f"http://localhost:8000/api/marketplace/callback/{plugin_id}"

    auth_url, state = plugin.get_auth_url(user_id=user_id, redirect_uri=backend_callback)
    return OAuthConnectResponse(
        authorization_url=auth_url,
        state=state,
        plugin_id=plugin_id,
    )


@router.get("/callback/{plugin_id}")
async def oauth_callback(
    plugin_id: str,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    user_id: Optional[str] = Query("guest_user"),
):
    """OAuth callback handler. Exchanges code for tokens and redirects back to React."""
    # Ensure redirect points to Next.js port 3000 if running locally
    frontend_base = settings.FRONTEND_URL
    if "localhost:5173" in frontend_base:
        frontend_base = "http://localhost:3000"
    frontend_redirect = f"{frontend_base}/marketplace"

    if error:
        logger.warning(f"OAuth failed for {plugin_id}: {error}")
        return RedirectResponse(f"{frontend_redirect}?error={error}&plugin_id={plugin_id}")

    if not code:
        return RedirectResponse(f"{frontend_redirect}?error=missing_code&plugin_id={plugin_id}")

    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        return RedirectResponse(f"{frontend_redirect}?error=plugin_not_found&plugin_id={plugin_id}")

    try:
        backend_callback = f"http://localhost:8000/api/marketplace/callback/{plugin_id}"
        credentials = await plugin.exchange_code(code=code, redirect_uri=backend_callback, state=state)
        plugin_manager.connect_user_plugin(user_id=user_id, plugin_id=plugin_id, raw_credentials=credentials)
        return RedirectResponse(f"{frontend_redirect}?connected={plugin_id}")
    except Exception as e:
        logger.error(f"Failed to exchange OAuth code for {plugin_id}: {e}", exc_info=True)
        return RedirectResponse(f"{frontend_redirect}?error=exchange_failed&plugin_id={plugin_id}")


# Direct manual connection endpoint for testing / mock credentials
class DirectConnectRequest(BaseModel):
    plugin_id: str
    access_token: str
    account_email: Optional[str] = "user@example.com"
    account_username: Optional[str] = "user"


@router.post("/connect-direct")
async def connect_direct(
    req: DirectConnectRequest,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Direct connect endpoint for development, testing, and mock accounts."""
    user_id = resolve_user_id(current_user)
    plugin = plugin_manager.get_plugin(req.plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{req.plugin_id}' not found")

    credentials = {
        "access_token": req.access_token,
        "account_id": f"acc_{req.plugin_id}_{user_id}",
        "account_email": req.account_email,
        "account_username": req.account_username,
        "avatar_url": None,
        "scopes": plugin.scopes,
    }
    conn = plugin_manager.connect_user_plugin(user_id=user_id, plugin_id=req.plugin_id, raw_credentials=credentials)
    return {"status": "connected", "plugin_id": req.plugin_id, "account_email": req.account_email}


@router.post("/disconnect/{plugin_id}")
async def disconnect_plugin(
    plugin_id: str,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Disconnect and revoke an active integration."""
    user_id = resolve_user_id(current_user)
    success = await plugin_manager.disconnect_user_plugin(user_id=user_id, plugin_id=plugin_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Integration '{plugin_id}' was not active")
    return {"status": "disconnected", "plugin_id": plugin_id}


# ---------------------------------------------------------------------------
# 3. Permissions & Approvals Management
# ---------------------------------------------------------------------------

@router.get("/permissions/{plugin_id}")
async def get_plugin_permissions(
    plugin_id: str,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Get list of tool permissions for a specific plugin."""
    user_id = resolve_user_id(current_user)
    return plugin_manager.list_permissions(user_id=user_id, plugin_id=plugin_id)


@router.post("/permissions")
async def update_permission(
    update: PluginPermissionUpdate,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Update permission level for a plugin tool (ALLOW, APPROVAL_REQUIRED, DENY)."""
    user_id = resolve_user_id(current_user)
    plugin_manager.set_permission(
        user_id=user_id,
        plugin_id=update.plugin_id,
        tool_name=update.tool_name,
        level=update.permission_level,
    )
    return {
        "status": "updated",
        "plugin_id": update.plugin_id,
        "tool_name": update.tool_name,
        "permission_level": update.permission_level.value,
    }


@router.post("/approvals/{approval_id}/approve")
async def approve_tool_execution(
    approval_id: str,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Approve a sensitive pending tool execution."""
    user_id = resolve_user_id(current_user)
    success = plugin_manager.approve_request(user_id=user_id, approval_id=approval_id)
    if not success:
        raise HTTPException(status_code=404, detail="Approval request not found or not owned by user")
    return {"status": "approved", "approval_id": approval_id}


@router.post("/approvals/{approval_id}/reject")
async def reject_tool_execution(
    approval_id: str,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Reject a pending tool execution."""
    user_id = resolve_user_id(current_user)
    success = plugin_manager.reject_request(user_id=user_id, approval_id=approval_id)
    if not success:
        raise HTTPException(status_code=404, detail="Approval request not found or not owned by user")
    return {"status": "rejected", "approval_id": approval_id}


# ---------------------------------------------------------------------------
# 4. Tool Execution & Audit Logging
# ---------------------------------------------------------------------------

@router.post("/execute", response_model=PluginExecuteResponse)
async def execute_plugin_tool(
    request: PluginExecuteRequest,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Execute a plugin tool subject to permissions, approval, and timeout constraints."""
    user_id = resolve_user_id(current_user)
    return await plugin_manager.execute_tool(
        user_id=user_id,
        plugin_id=request.plugin_id,
        tool_name=request.tool_name,
        arguments=request.arguments,
        approval_token=request.approval_token,
    )


@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = Query(50, le=200),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Retrieve audit history of executed plugin actions."""
    user_id = resolve_user_id(current_user)
    return plugin_manager.list_audit_logs(user_id=user_id, limit=limit)
