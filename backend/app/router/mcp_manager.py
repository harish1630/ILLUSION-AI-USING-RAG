"""MCP (Model Context Protocol) Discovery and Client Manager – Phase 1 Stub.

Provides the interface for future MCP server discovery and tool integration.
In Phase 1 this is a no-op skeleton that reports zero MCP tools.
Phase 2 will implement actual discovery, connection pooling, and tool proxying.
"""

from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger


class MCPToolProxy:
    """Represents a single tool exposed by an MCP server."""

    def __init__(self, name: str, description: str, server_url: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.server_url = server_url
        self.parameters = parameters

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "server_url": self.server_url,
            "parameters": self.parameters,
        }


class MCPManager:
    """Manages discovery and invocation of tools from MCP servers.

    Phase 1: Stub returning empty tool lists.
    Phase 2: Real discovery via stdio / SSE transport.
    """

    def __init__(self):
        self._discovered_tools: List[MCPToolProxy] = []
        self._servers: List[Dict[str, Any]] = []
        self._enabled = settings.MCP_DISCOVERY_ENABLED

    async def discover(self) -> List[MCPToolProxy]:
        """Discover tools from configured MCP servers.

        Returns empty list in Phase 1.
        """
        if not self._enabled:
            logger.debug("MCP discovery is disabled (MCP_DISCOVERY_ENABLED=False).")
            return []

        # Phase 2: iterate configured MCP servers, initialise transport, list tools
        logger.info("MCP discovery placeholder – no servers configured yet.")
        return []

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all discovered MCP tools in LLM-friendly format."""
        return [t.to_dict() for t in self._discovered_tools]

    async def invoke(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Invoke an MCP tool by name.

        Returns None in Phase 1.
        """
        logger.warning(f"MCP invoke called for '{tool_name}' but MCP is not yet implemented (Phase 2).")
        return None

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    @property
    def tool_count(self) -> int:
        return len(self._discovered_tools)


# Global singleton
mcp_manager = MCPManager()
