"""Pydantic Schemas for Illusion AI Plugin Marketplace."""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PermissionLevel(str, Enum):
    ALLOW = "ALLOW"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    DENY = "DENY"


class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DENIED = "DENIED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


class PluginCategory(str, Enum):
    EMAIL = "email"
    DEVELOPER = "developer"
    PRODUCTIVITY = "productivity"
    COMMUNICATION = "communication"
    TOOLS = "tools"


class PluginToolDefinition(BaseModel):
    tool_name: str
    qualified_name: str
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    is_sensitive: bool = False
    default_permission: PermissionLevel = PermissionLevel.DENY


class PluginCatalogItem(BaseModel):
    id: str
    name: str
    display_name: str
    description: str
    category: str
    icon: str
    auth_type: str
    scopes: List[str] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    is_active: bool = True
    is_connected: bool = False
    account_info: Optional[Dict[str, Any]] = None
    connected_at: Optional[str] = None
    tools: List[PluginToolDefinition] = Field(default_factory=list)


class UserIntegrationResponse(BaseModel):
    id: str
    user_id: str
    plugin_id: str
    plugin_name: str
    plugin_display_name: str
    plugin_icon: str
    account_id: Optional[str] = None
    account_email: Optional[str] = None
    account_username: Optional[str] = None
    avatar_url: Optional[str] = None
    status: str = "connected"
    scopes: List[str] = Field(default_factory=list)
    connected_at: str
    updated_at: str


class PluginPermissionUpdate(BaseModel):
    plugin_id: str
    tool_name: str
    permission_level: PermissionLevel


class PluginExecuteRequest(BaseModel):
    plugin_id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    approval_token: Optional[str] = None


class PluginExecuteResponse(BaseModel):
    tool_name: str
    plugin_id: str
    status: ExecutionStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    approval_id: Optional[str] = None
    execution_time_ms: float = 0.0


class OAuthConnectResponse(BaseModel):
    authorization_url: str
    state: str
    plugin_id: str


class AuditLogItem(BaseModel):
    id: str
    user_id: str
    plugin_id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    status: ExecutionStatus
    result: Optional[Any] = None
    error_message: Optional[str] = None
    duration_ms: float = 0.0
    created_at: str


class ApprovalItem(BaseModel):
    id: str
    user_id: str
    plugin_id: str
    tool_name: str
    arguments: Dict[str, Any]
    status: str  # 'PENDING', 'APPROVED', 'REJECTED'
    created_at: str
    expires_at: str
