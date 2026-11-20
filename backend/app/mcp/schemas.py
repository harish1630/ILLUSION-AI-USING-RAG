"""Pydantic schemas for Model Context Protocol (MCP) server management, tools, permissions, and execution."""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class MCPTransportType(str, Enum):
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"
    CUSTOM = "custom"


class MCPServerStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"


class PermissionLevel(str, Enum):
    ALLOW = "ALLOW"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    DENY = "DENY"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DENIED = "DENIED"
    PENDING_APPROVAL = "PENDING_APPROVAL"


# ---------------------------------------------------------------------------
# Server Schemas
# ---------------------------------------------------------------------------

class MCPServerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Unique human-readable server name")
    transport: MCPTransportType = Field(default=MCPTransportType.STDIO)
    command: Optional[str] = Field(default=None, description="Command executable for STDIO (e.g. 'python', 'npx')")
    args: List[str] = Field(default_factory=list, description="Command arguments (e.g. ['path/to/server.py'])")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables passed to process")
    url: Optional[str] = Field(default=None, description="Endpoint URL for SSE / HTTP transport")
    auto_connect: bool = Field(default=True, description="Connect immediately upon creation")


class MCPServerResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    user_id: Optional[str] = None
    transport: Optional[MCPTransportType] = None
    transport_type: Optional[MCPTransportType] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    status: MCPServerStatus
    tool_count: int = 0
    tools_count: int = 0
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Tool Schemas
# ---------------------------------------------------------------------------

class MCPToolDefinition(BaseModel):
    id: Optional[str] = None
    server_id: str
    server_name: str
    tool_name: str
    name: Optional[str] = None
    qualified_name: str  # e.g. "illusion_custom::get_project_info"
    description: str = ""
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    permission_level: PermissionLevel = PermissionLevel.DENY
    discovered_at: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.name:
            self.name = self.tool_name
        if not self.id:
            self.id = self.qualified_name
        if not self.discovered_at:
            from datetime import datetime, timezone
            self.discovered_at = datetime.now(timezone.utc).isoformat()


class MCPToolExecuteRequest(BaseModel):
    server_id: Optional[str] = None
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    approval_id: Optional[str] = None


class MCPToolExecuteResponse(BaseModel):
    tool_name: str
    server_name: Optional[str] = ""
    server_id: Optional[str] = ""
    status: ExecutionStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    approval_id: Optional[str] = None
    execution_time_ms: float = 0.0

    def model_post_init(self, __context: Any) -> None:
        if not self.server_name and self.server_id:
            self.server_name = self.server_id
        elif not self.server_id and self.server_name:
            self.server_id = self.server_name


# ---------------------------------------------------------------------------
# Permissions & Approvals Schemas
# ---------------------------------------------------------------------------

class MCPPermissionUpdate(BaseModel):
    server_id: str
    tool_name: str
    permission_level: PermissionLevel


class MCPApprovalResponse(BaseModel):
    id: str
    user_id: str
    server_id: str
    server_name: str
    tool_name: str
    arguments: Dict[str, Any]
    reason: str
    status: ApprovalStatus
    created_at: str
    resolved_at: Optional[str] = None


class MCPExecutionLogResponse(BaseModel):
    id: str
    user_id: str
    server_name: str
    tool_name: str
    execution_status: ExecutionStatus
    execution_time_ms: float
    error_message: Optional[str] = None
    created_at: str


class MCPHealthSummary(BaseModel):
    status: str
    total_servers: int = 0
    connected_servers: int = 0
    active_servers: int = 0
    total_tools: int = 0
    pending_approvals: int = 0
    recent_executions_count: int = 0
    default_policy: str = "DENY"

