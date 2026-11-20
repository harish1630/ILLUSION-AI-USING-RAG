"""Client Connection Manager for MCP Servers.

Supports:
- In-process custom servers (illusion_custom direct execution)
- STDIO subprocess transports (stdio_client, StdioServerParameters)
- Streamable HTTP / SSE remote servers
"""

import asyncio
import logging
import sys
from typing import Dict, Any, Optional, List
try:
    from app.mcp.schemas import MCPTransportType, MCPServerStatus
except ImportError:
    from backend.app.mcp.schemas import MCPTransportType, MCPServerStatus

logger = logging.getLogger(__name__)


class MCPClientConnection:
    """Represents an active connection to an MCP server."""

    def __init__(self, server_id: str, transport_type: MCPTransportType, config: Dict[str, Any]):
        self.server_id = server_id
        self.transport_type = transport_type
        self.config = config
        self.status = MCPServerStatus.DISCONNECTED
        self.error_message: Optional[str] = None
        self._session = None

    async def connect(self):
        """Establish connection based on transport type."""
        try:
            self.status = MCPServerStatus.CONNECTING

            if self.server_id == "illusion_custom" or self.transport_type == MCPTransportType.CUSTOM:
                # Direct in-process execution with custom server
                from backend.app.mcp_servers.custom_server import server as custom_srv
                self._session = custom_srv
                self.status = MCPServerStatus.CONNECTED
                self.error_message = None
                logger.info(f"Connected to in-process custom MCP server '{self.server_id}'")
                return

            if self.transport_type == MCPTransportType.STDIO:
                # Check command configuration
                command = self.config.get("command", sys.executable)
                args = self.config.get("args", [])
                env = self.config.get("env", None)

                from mcp.client.stdio import StdioServerParameters
                params = StdioServerParameters(command=command, args=args, env=env)
                # Store connection params
                self._session = params
                self.status = MCPServerStatus.CONNECTED
                self.error_message = None
                logger.info(f"STDIO MCP server '{self.server_id}' configured with command: {command}")
                return

            if self.transport_type in (MCPTransportType.SSE, MCPTransportType.STREAMABLE_HTTP):
                url = self.config.get("url")
                if not url:
                    raise ValueError(f"URL is required for {self.transport_type.value} transport")
                self.status = MCPServerStatus.CONNECTED
                self.error_message = None
                logger.info(f"HTTP/SSE MCP server '{self.server_id}' configured with endpoint: {url}")
                return

            raise ValueError(f"Unsupported transport type: {self.transport_type}")

        except Exception as e:
            self.status = MCPServerStatus.ERROR
            self.error_message = str(e)
            logger.error(f"Failed to connect MCP server '{self.server_id}': {e}", exc_info=True)
            raise

    async def disconnect(self):
        """Disconnect and clean up resources."""
        self.status = MCPServerStatus.DISCONNECTED
        self._session = None
        logger.info(f"Disconnected MCP server '{self.server_id}'")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on this server."""
        if self.status != MCPServerStatus.CONNECTED:
            raise RuntimeError(f"Server '{self.server_id}' is not connected (status: {self.status.value})")

        if self.server_id == "illusion_custom" or self.transport_type == MCPTransportType.CUSTOM:
            from backend.app.mcp_servers import custom_server
            fn = getattr(custom_server, tool_name, None)
            if callable(fn):
                if asyncio.iscoroutinefunction(fn):
                    return await fn(**arguments)
                return fn(**arguments)
            raise ValueError(f"Tool '{tool_name}' not found on server '{self.server_id}'")

        raise NotImplementedError(f"Remote transport tool invocation for '{self.server_id}' not yet implemented")


class MCPClientManager:
    """Manages pool of MCP server connections."""

    def __init__(self):
        self._connections: Dict[str, MCPClientConnection] = {}

    def get_connection(self, server_id: str) -> Optional[MCPClientConnection]:
        return self._connections.get(server_id)

    async def connect_server(
        self,
        server_id: str,
        transport_type: MCPTransportType,
        config: Dict[str, Any],
    ) -> MCPClientConnection:
        """Establish connection to an MCP server."""
        conn = MCPClientConnection(server_id, transport_type, config)
        await conn.connect()
        self._connections[server_id] = conn
        return conn

    async def disconnect_server(self, server_id: str):
        """Disconnect a server and remove from pool."""
        conn = self._connections.get(server_id)
        if conn:
            await conn.disconnect()
            self._connections.pop(server_id, None)

    def list_connections(self) -> List[MCPClientConnection]:
        return list(self._connections.values())


# Global singleton instance
mcp_client_manager = MCPClientManager()
