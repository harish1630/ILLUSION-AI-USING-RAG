"""MCP Module Exports for Illusion AI."""

try:
    from app.mcp.schemas import (
        MCPTransportType,
        MCPServerStatus,
        PermissionLevel,
        ApprovalStatus,
        ExecutionStatus,
        MCPServerCreate,
        MCPServerResponse,
        MCPToolDefinition,
        MCPToolExecuteRequest,
        MCPToolExecuteResponse,
        MCPPermissionUpdate,
        MCPApprovalResponse,
        MCPExecutionLogResponse,
        MCPHealthSummary,
    )
    from app.mcp.manager import mcp_manager
    from app.mcp.registry import mcp_tool_registry
    from app.mcp.permissions import permission_manager
    from app.mcp.approval import approval_queue
    from app.mcp.executor import mcp_executor
except ImportError:
    from backend.app.mcp.schemas import (
        MCPTransportType,
        MCPServerStatus,
        PermissionLevel,
        ApprovalStatus,
        ExecutionStatus,
        MCPServerCreate,
        MCPServerResponse,
        MCPToolDefinition,
        MCPToolExecuteRequest,
        MCPToolExecuteResponse,
        MCPPermissionUpdate,
        MCPApprovalResponse,
        MCPExecutionLogResponse,
        MCPHealthSummary,
    )
    from backend.app.mcp.manager import mcp_manager
    from backend.app.mcp.registry import mcp_tool_registry
    from backend.app.mcp.permissions import permission_manager
    from backend.app.mcp.approval import approval_queue
    from backend.app.mcp.executor import mcp_executor

__all__ = [
    "mcp_manager",
    "mcp_tool_registry",
    "permission_manager",
    "approval_queue",
    "mcp_executor",
    "MCPTransportType",
    "MCPServerStatus",
    "PermissionLevel",
    "ApprovalStatus",
    "ExecutionStatus",
    "MCPServerCreate",
    "MCPServerResponse",
    "MCPToolDefinition",
    "MCPToolExecuteRequest",
    "MCPToolExecuteResponse",
    "MCPPermissionUpdate",
    "MCPApprovalResponse",
    "MCPExecutionLogResponse",
    "MCPHealthSummary",
]
