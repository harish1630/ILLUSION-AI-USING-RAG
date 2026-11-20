"""Dynamic tool discovery from MCP servers."""

from typing import List, Dict, Any, Optional
import logging
try:
    from app.mcp.schemas import MCPToolDefinition
except ImportError:
    from backend.app.mcp.schemas import MCPToolDefinition

logger = logging.getLogger(__name__)


class MCPDiscovery:
    """Discovers tools, schemas, and capabilities from MCP servers."""

    @staticmethod
    def parse_mcp_tool(server_id: str, tool_obj: Any) -> MCPToolDefinition:
        """Convert an MCP Tool object or dict into an MCPToolDefinition."""
        name = getattr(tool_obj, "name", None) or (tool_obj.get("name") if isinstance(tool_obj, dict) else "unknown")
        description = getattr(tool_obj, "description", None) or (tool_obj.get("description") if isinstance(tool_obj, dict) else "")
        input_schema = getattr(tool_obj, "inputSchema", None) or getattr(tool_obj, "input_schema", None) or (tool_obj.get("inputSchema") if isinstance(tool_obj, dict) else {})
        
        # Ensure schema is dictionary
        if not isinstance(input_schema, dict):
            input_schema = {"type": "object", "properties": {}}

        # Server-qualified tool name
        qualified_name = f"{server_id}:{name}"

        return MCPToolDefinition(
            server_id=server_id,
            server_name=server_id,
            tool_name=name,
            qualified_name=qualified_name,
            description=description or f"MCP tool {name} provided by server {server_id}",
            input_schema=input_schema,
            is_enabled=True,
        )

    @classmethod
    async def discover_tools_from_session(cls, server_id: str, session: Any) -> List[MCPToolDefinition]:
        """Query an active MCP ClientSession for its available tools."""
        try:
            result = await session.list_tools()
            tools_list = getattr(result, "tools", []) or []
            discovered = [cls.parse_mcp_tool(server_id, t) for t in tools_list]
            logger.info(f"Discovered {len(discovered)} tools from MCP server '{server_id}'")
            return discovered
        except Exception as e:
            logger.error(f"Failed to discover tools from MCP server '{server_id}': {e}", exc_info=True)
            return []
