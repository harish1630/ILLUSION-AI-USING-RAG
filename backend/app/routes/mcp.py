"""FastAPI routes for Model Context Protocol (MCP) in Illusion AI.

Endpoints:
- /api/mcp/servers [GET, POST]
- /api/mcp/servers/{server_id} [GET]
- /api/mcp/servers/{server_id}/connect [POST]
- /api/mcp/servers/{server_id}/disconnect [POST]
- /api/mcp/tools [GET]
- /api/mcp/tools/execute [POST]
- /api/mcp/permissions [GET, POST]
- /api/mcp/approvals [GET]
- /api/mcp/approvals/{approval_id}/approve [POST]
- /api/mcp/approvals/{approval_id}/reject [POST]
- /api/mcp/logs [GET]
- /api/mcp/health [GET]
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

try:
    from app.mcp import (
        mcp_manager,
        mcp_tool_registry,
        permission_manager,
        approval_queue,
        mcp_executor,
        MCPServerCreate,
        MCPServerResponse,
        MCPToolDefinition,
        MCPToolExecuteRequest,
        MCPToolExecuteResponse,
        MCPPermissionUpdate,
        MCPApprovalResponse,
        MCPExecutionLogResponse,
        MCPHealthSummary,
        PermissionLevel,
        ApprovalStatus,
    )
except ImportError:
    from backend.app.mcp import (
        mcp_manager,
        mcp_tool_registry,
        permission_manager,
        approval_queue,
        mcp_executor,
        MCPServerCreate,
        MCPServerResponse,
        MCPToolDefinition,
        MCPToolExecuteRequest,
        MCPToolExecuteResponse,
        MCPPermissionUpdate,
        MCPApprovalResponse,
        MCPExecutionLogResponse,
        MCPHealthSummary,
        PermissionLevel,
        ApprovalStatus,
    )
from app.routes.auth import get_current_user_optional, CurrentUser

router = APIRouter(prefix="/api/mcp", tags=["Model Context Protocol (MCP)"])


@router.get("/health", response_model=MCPHealthSummary)
async def get_mcp_health():
    """Get overall MCP status and health metrics."""
    await mcp_manager.initialize()
    return mcp_manager.get_health_summary()


@router.get("/servers", response_model=List[MCPServerResponse])
async def list_mcp_servers():
    """List all registered MCP servers."""
    await mcp_manager.initialize()
    return mcp_manager.list_servers()


@router.post("/servers", response_model=MCPServerResponse, status_code=status.HTTP_201_CREATED)
async def create_mcp_server(
    server_in: MCPServerCreate,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Register a new MCP server configuration."""
    await mcp_manager.initialize()
    try:
        return await mcp_manager.register_server(server_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/servers/{server_id}", response_model=MCPServerResponse)
async def get_mcp_server(server_id: str):
    """Get server configuration by ID."""
    await mcp_manager.initialize()
    server = mcp_manager.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail=f"MCP Server '{server_id}' not found")
    return server


@router.post("/servers/{server_id}/connect")
async def connect_mcp_server(server_id: str):
    """Connect to an MCP server and trigger dynamic tool discovery."""
    await mcp_manager.initialize()
    success = await mcp_manager.connect_server(server_id)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to connect to MCP server '{server_id}'")
    tools = mcp_tool_registry.list_tools(server_id)
    return {
        "status": "connected",
        "server_id": server_id,
        "tools_discovered": len(tools),
    }


@router.post("/servers/{server_id}/disconnect")
async def disconnect_mcp_server(server_id: str):
    """Disconnect an MCP server and remove its tools."""
    await mcp_manager.initialize()
    await mcp_manager.disconnect_server(server_id)
    return {"status": "disconnected", "server_id": server_id}


@router.get("/tools", response_model=List[MCPToolDefinition])
async def list_mcp_tools(server_id: Optional[str] = Query(None, description="Filter tools by server ID")):
    """List all discovered MCP tools."""
    await mcp_manager.initialize()
    return mcp_tool_registry.list_tools(server_id)


@router.post("/tools/execute", response_model=MCPToolExecuteResponse)
async def execute_mcp_tool(
    request: MCPToolExecuteRequest,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Execute an MCP tool subject to permissions, approval, and 15s timeout."""
    await mcp_manager.initialize()
    user_id = current_user.sub if current_user else "default_user"
    return await mcp_manager.execute_tool(request, user_id=user_id)


@router.get("/permissions")
async def list_mcp_permissions(
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """List configured tool permissions."""
    user_id = current_user.sub if current_user else None
    return permission_manager.list_permissions(user_id=user_id)


@router.post("/permissions")
async def set_mcp_permission(
    perm_in: MCPPermissionUpdate,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Update permission level for a tool (ALLOW, APPROVAL_REQUIRED, DENY)."""
    user_id = perm_in.user_id or (current_user.sub if current_user else "*")
    permission_manager.set_permission(
        user_id=user_id,
        server_id=perm_in.server_id,
        tool_name=perm_in.tool_name,
        level=perm_in.permission_level,
    )
    return {
        "status": "updated",
        "user_id": user_id,
        "server_id": perm_in.server_id,
        "tool_name": perm_in.tool_name,
        "permission_level": perm_in.permission_level.value,
    }


@router.get("/approvals")
async def list_mcp_approvals(
    status_filter: Optional[ApprovalStatus] = Query(None, description="Filter approvals by status"),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """List pending and historical human-in-the-loop approvals."""
    user_id = current_user.sub if current_user else None
    return approval_queue.list_requests(user_id=user_id, status=status_filter)


@router.post("/approvals/{approval_id}/approve")
async def approve_mcp_request(
    approval_id: str,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Approve a pending tool execution request."""
    reviewer_id = current_user.sub if current_user else "default_user"
    req = approval_queue.resolve_request(approval_id, approved=True, reviewer_id=reviewer_id)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return req


@router.post("/approvals/{approval_id}/reject")
async def reject_mcp_request(
    approval_id: str,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Reject a pending tool execution request."""
    reviewer_id = current_user.sub if current_user else "default_user"
    req = approval_queue.resolve_request(approval_id, approved=False, reviewer_id=reviewer_id)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return req


@router.get("/logs")
async def list_mcp_logs(
    limit: int = Query(50, ge=1, le=200),
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Retrieve recent MCP execution audit logs."""
    user_id = current_user.sub if current_user else None
    return mcp_executor.list_logs(user_id=user_id, limit=limit)
