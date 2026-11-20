"""Dynamic Tool Registry for MCP tools in Illusion AI.

Maintains registered MCP tools, handles server-qualified identifiers,
generates tool schemas for the LLM, and integrates with the router.
"""

from typing import Dict, List, Optional, Any
import logging
try:
    from app.mcp.schemas import MCPToolDefinition
except ImportError:
    from backend.app.mcp.schemas import MCPToolDefinition

logger = logging.getLogger(__name__)


class MCPToolRegistry:
    """Dynamic registry storing discovered MCP tools and their schemas."""

    def __init__(self):
        # Key: qualified_name (e.g., 'illusion_custom:calculate' or just 'calculate' if unique) -> MCPToolDefinition
        self._tools: Dict[str, MCPToolDefinition] = {}
        # Key: server_id -> list of tool names
        self._server_tools: Dict[str, List[str]] = {}

    def register_tool(self, tool: MCPToolDefinition):
        """Register or update a tool definition."""
        t_name = getattr(tool, "tool_name", None) or getattr(tool, "name", "")
        qualified_name = tool.qualified_name or f"{tool.server_id}:{t_name}"
        self._tools[qualified_name] = tool
        # Also map bare name if not already conflicting
        if t_name not in self._tools:
            self._tools[t_name] = tool

        if tool.server_id not in self._server_tools:
            self._server_tools[tool.server_id] = []
        if t_name not in self._server_tools[tool.server_id]:
            self._server_tools[tool.server_id].append(t_name)

        logger.debug(f"Registered MCP tool: {qualified_name}")

    def register_tools(self, server_id: str, tools: List[MCPToolDefinition]):
        """Batch register tools for a server, replacing stale entries."""
        self.remove_server_tools(server_id)
        for t in tools:
            self.register_tool(t)
        logger.info(f"Registered {len(tools)} tools for server '{server_id}'")

    def remove_server_tools(self, server_id: str):
        """Remove all tools associated with a server when disconnected."""
        tool_names = self._server_tools.pop(server_id, [])
        for name in tool_names:
            qualified = f"{server_id}:{name}"
            self._tools.pop(qualified, None)
            # Remove bare name if it pointed to this server's tool
            if name in self._tools and self._tools[name].server_id == server_id:
                self._tools.pop(name, None)
        logger.info(f"Deregistered {len(tool_names)} tools for server '{server_id}'")

    def get_tool(self, identifier: str) -> Optional[MCPToolDefinition]:
        """Retrieve tool by bare name ('calculate') or qualified name ('illusion_custom:calculate')."""
        return self._tools.get(identifier)

    def list_tools(self, server_id: Optional[str] = None) -> List[MCPToolDefinition]:
        """List all unique registered tools, optionally filtered by server."""
        seen = set()
        result = []
        for key, tool in self._tools.items():
            if ":" not in key:
                continue  # Skip bare alias to avoid duplicate entries in listing
            if server_id and tool.server_id != server_id:
                continue
            if tool.name not in seen or tool.server_id not in seen:
                seen.add((tool.server_id, tool.name))
                result.append(tool)
        return result

    def get_tool_schemas_for_llm(self) -> List[Dict[str, Any]]:
        """Format all active MCP tools for LLM system prompts and function definitions."""
        schemas = []
        for tool in self.list_tools():
            if not tool.is_enabled:
                continue
            schemas.append({
                "name": f"{tool.server_id}__{tool.name}",
                "server": tool.server_id,
                "tool_name": tool.name,
                "description": f"[{tool.server_id}] {tool.description}",
                "parameters": tool.input_schema,
            })
        return schemas


# Global singleton instance
mcp_tool_registry = MCPToolRegistry()
