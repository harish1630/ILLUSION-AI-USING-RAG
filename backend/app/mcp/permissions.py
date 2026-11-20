"""Permission and policy control for MCP tools in Illusion AI.

Enforces 3 levels:
- ALLOW
- APPROVAL_REQUIRED
- DENY (Strict Default)

Rules can be configured per user, server, and tool.
"""

from typing import Dict, Any, Optional, List
import logging
try:
    from app.mcp.schemas import PermissionLevel
except ImportError:
    from backend.app.mcp.schemas import PermissionLevel

logger = logging.getLogger(__name__)


class MCPPermissionManager:
    """Evaluates and manages execution permissions for MCP tools."""

    def __init__(self):
        # Key: (user_id, server_id, tool_name) -> PermissionLevel
        # Wildcard "*" can be used for server_id and tool_name
        self._rules: Dict[tuple, PermissionLevel] = {}
        # Default policy is strictly DENY as required
        self.default_policy: PermissionLevel = PermissionLevel.DENY
        # Pre-seed default safe allowances for illusion_custom diagnostic tools
        self._seed_default_permissions()

    def _seed_default_permissions(self):
        """Seed safe default permissions for illusion_custom diagnostic tools."""
        safe_tools = ["get_project_info", "list_project_modules", "calculate", "get_system_status"]
        for tool in safe_tools:
            # Safe read-only / arithmetic tools on illusion_custom are ALLOWed by default for all users
            self._rules[("*", "illusion_custom", tool)] = PermissionLevel.ALLOW

    def set_permission(
        self,
        user_id: str,
        server_id: str,
        tool_name: str,
        level: PermissionLevel,
    ):
        """Set a permission rule."""
        self._rules[(user_id, server_id, tool_name)] = level
        logger.info(f"Set permission ({user_id}, {server_id}, {tool_name}) -> {level.value}")

    def get_permission(
        self,
        user_id: str,
        server_id: str,
        tool_name: str,
    ) -> PermissionLevel:
        """Evaluate permission using hierarchy:
        1. Exact match: (user_id, server_id, tool_name)
        2. User server wildcard: (user_id, server_id, "*")
        3. Global tool match: ("*", server_id, tool_name)
        4. Global server match: ("*", server_id, "*")
        5. Global wildcard: ("*", "*", "*")
        6. Default policy: DENY
        """
        # 1. Exact match
        if (user_id, server_id, tool_name) in self._rules:
            return self._rules[(user_id, server_id, tool_name)]

        # 2. User server wildcard
        if (user_id, server_id, "*") in self._rules:
            return self._rules[(user_id, server_id, "*")]

        # 3. Global tool match
        if ("*", server_id, tool_name) in self._rules:
            return self._rules[("*", server_id, tool_name)]

        # 4. Global server match
        if ("*", server_id, "*") in self._rules:
            return self._rules[("*", server_id, "*")]

        # 5. Global wildcard
        if ("*", "*", "*") in self._rules:
            return self._rules[("*", "*", "*")]

        # 6. Strict Default: DENY
        return self.default_policy

    def list_permissions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all registered permission rules."""
        result = []
        for (u, s, t), level in self._rules.items():
            if user_id is None or u == user_id or u == "*":
                result.append({
                    "user_id": u,
                    "server_id": s,
                    "tool_name": t,
                    "permission_level": level.value,
                })
        return result


# Global singleton instance
permission_manager = MCPPermissionManager()
