"""Plugin Marketplace Core Package for Illusion AI."""

from app.plugins.schemas import (
    PermissionLevel,
    ExecutionStatus,
    PluginCategory,
    PluginToolDefinition,
    PluginCatalogItem,
    UserIntegrationResponse,
    PluginPermissionUpdate,
    PluginExecuteRequest,
    PluginExecuteResponse,
    OAuthConnectResponse,
    AuditLogItem,
    ApprovalItem,
)
from app.plugins.base import BasePlugin
from app.plugins.catalog import DEFAULT_CATALOG
from app.plugins.manager import plugin_manager, PluginManager

__all__ = [
    "PermissionLevel",
    "ExecutionStatus",
    "PluginCategory",
    "PluginToolDefinition",
    "PluginCatalogItem",
    "UserIntegrationResponse",
    "PluginPermissionUpdate",
    "PluginExecuteRequest",
    "PluginExecuteResponse",
    "OAuthConnectResponse",
    "AuditLogItem",
    "ApprovalItem",
    "BasePlugin",
    "DEFAULT_CATALOG",
    "plugin_manager",
    "PluginManager",
]
