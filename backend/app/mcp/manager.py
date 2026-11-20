"""High-level Orchestration Manager for Model Context Protocol (MCP) in Illusion AI.

Coordinates:
- Server configuration, connection, and disconnection
- Dynamic tool discovery and registration
- Permission enforcement and approval workflows
- Execution dispatching and audit logging
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging

try:
    from app.mcp.schemas import (
        MCPServerCreate,
        MCPServerResponse,
        MCPTransportType,
        MCPServerStatus,
        MCPToolDefinition,
        MCPToolExecuteRequest,
        MCPToolExecuteResponse,
        MCPHealthSummary,
        PermissionLevel,
    )
    from app.mcp.client import mcp_client_manager
    from app.mcp.registry import mcp_tool_registry
    from app.mcp.discovery import MCPDiscovery
    from app.mcp.executor import mcp_executor
    from app.mcp.permissions import permission_manager
    from app.mcp.approval import approval_queue
except ImportError:
    from backend.app.mcp.schemas import (
        MCPServerCreate,
        MCPServerResponse,
        MCPTransportType,
        MCPServerStatus,
        MCPToolDefinition,
        MCPToolExecuteRequest,
        MCPToolExecuteResponse,
        MCPHealthSummary,
        PermissionLevel,
    )
    from backend.app.mcp.client import mcp_client_manager
    from backend.app.mcp.registry import mcp_tool_registry
    from backend.app.mcp.discovery import MCPDiscovery
    from backend.app.mcp.executor import mcp_executor
    from backend.app.mcp.permissions import permission_manager
    from backend.app.mcp.approval import approval_queue

logger = logging.getLogger(__name__)


class MCPManager:
    """Central MCP orchestrator for Illusion AI."""

    def __init__(self):
        self._servers: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize built-in custom MCP server and auto-connect default services."""
        if self._initialized:
            return

        logger.info("Initializing Illusion AI MCP Manager...")

        # Register default custom MCP server: illusion_custom
        custom_server_config = {
            "id": "illusion_custom",
            "name": "Illusion Custom Diagnostics",
            "description": "Built-in MCP server providing project info, module inspection, safe math calculation, and system diagnostics",
            "transport_type": MCPTransportType.CUSTOM.value,
            "config": {},
            "status": MCPServerStatus.DISCONNECTED.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._servers["illusion_custom"] = custom_server_config

        # Connect illusion_custom
        await self.connect_server("illusion_custom")
        self._initialized = True

    async def register_server(self, server_in: MCPServerCreate) -> MCPServerResponse:
        """Register a new MCP server configuration and optionally auto-connect."""
        server_id = server_in.name.lower().replace(" ", "_")
        now = datetime.now(timezone.utc).isoformat()
        server_data = {
            "id": server_id,
            "name": server_in.name,
            "description": server_in.description or "",
            "transport_type": server_in.transport_type.value,
            "config": server_in.config,
            "status": MCPServerStatus.DISCONNECTED.value,
            "created_at": now,
            "updated_at": now,
        }
        self._servers[server_id] = server_data

        if server_in.auto_connect:
            await self.connect_server(server_id)

        tools_count = len(mcp_tool_registry.list_tools(server_id))
        return MCPServerResponse(
            id=server_id,
            name=server_data["name"],
            description=server_data["description"],
            transport_type=MCPTransportType(server_data["transport_type"]),
            status=MCPServerStatus(server_data["status"]),
            config=server_data["config"],
            tools_count=tools_count,
            created_at=server_data["created_at"],
            updated_at=server_data["updated_at"],
        )

    async def connect_server(self, server_id: str) -> bool:
        """Connect to an MCP server and trigger dynamic tool discovery."""
        server_data = self._servers.get(server_id)
        if not server_data:
            raise ValueError(f"Server '{server_id}' not found")

        transport = MCPTransportType(server_data["transport_type"])
        config = server_data.get("config", {})

        try:
            conn = await mcp_client_manager.connect_server(server_id, transport, config)
            server_data["status"] = MCPServerStatus.CONNECTED.value
            server_data["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Dynamic tool discovery
            if server_id == "illusion_custom":
                from backend.app.mcp_servers.custom_server import server as custom_srv
                # Discover tools from custom_server
                tools = []
                for tool_name, tool_item in getattr(custom_srv, "_tool_manager", {})._tools.items() if hasattr(custom_srv, "_tool_manager") else []:
                    tools.append(MCPDiscovery.parse_mcp_tool(server_id, tool_item))
                
                # If _tool_manager was private or empty, statically register the 4 known tools
                if not tools:
                    tools = [
                        MCPToolDefinition(
                            tool_name="get_project_info",
                            server_id="illusion_custom",
                            server_name="illusion_custom",
                            qualified_name="illusion_custom:get_project_info",
                            description="Return Illusion AI project information and capabilities",
                            input_schema={"type": "object", "properties": {}},
                        ),
                        MCPToolDefinition(
                            tool_name="list_project_modules",
                            server_id="illusion_custom",
                            server_name="illusion_custom",
                            qualified_name="illusion_custom:list_project_modules",
                            description="Return available backend and frontend modules",
                            input_schema={"type": "object", "properties": {}},
                        ),
                        MCPToolDefinition(
                            tool_name="calculate",
                            server_id="illusion_custom",
                            server_name="illusion_custom",
                            qualified_name="illusion_custom:calculate",
                            description="Perform safe mathematical calculations without eval()",
                            input_schema={
                                "type": "object",
                                "properties": {"expression": {"type": "string", "description": "Math expression"}},
                                "required": ["expression"],
                            },
                        ),
                        MCPToolDefinition(
                            tool_name="get_system_status",
                            server_id="illusion_custom",
                            server_name="illusion_custom",
                            qualified_name="illusion_custom:get_system_status",
                            description="Return application health and configured service status (zero credentials exposed)",
                            input_schema={"type": "object", "properties": {}},
                        ),
                    ]
                mcp_tool_registry.register_tools(server_id, tools)
            else:
                # Discover from remote session
                if conn._session:
                    tools = await MCPDiscovery.discover_tools_from_session(server_id, conn._session)
                    mcp_tool_registry.register_tools(server_id, tools)

            logger.info(f"Successfully connected MCP server '{server_id}' and discovered tools")
            return True

        except Exception as e:
            server_data["status"] = MCPServerStatus.ERROR.value
            logger.error(f"Error connecting server '{server_id}': {e}", exc_info=True)
            return False

    async def disconnect_server(self, server_id: str):
        """Disconnect server and purge stale tools."""
        server_data = self._servers.get(server_id)
        if server_data:
            server_data["status"] = MCPServerStatus.DISCONNECTED.value
            server_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await mcp_client_manager.disconnect_server(server_id)
        mcp_tool_registry.remove_server_tools(server_id)
        logger.info(f"Disconnected server '{server_id}' and removed tools")

    def list_servers(self) -> List[MCPServerResponse]:
        """List all configured MCP servers."""
        responses = []
        for s_id, s in self._servers.items():
            tools_count = len(mcp_tool_registry.list_tools(s_id))
            responses.append(
                MCPServerResponse(
                    id=s_id,
                    name=s["name"],
                    description=s["description"],
                    transport_type=MCPTransportType(s["transport_type"]),
                    status=MCPServerStatus(s["status"]),
                    config=s["config"],
                    tools_count=tools_count,
                    created_at=s["created_at"],
                    updated_at=s["updated_at"],
                )
            )
        return responses

    def get_server(self, server_id: str) -> Optional[MCPServerResponse]:
        s = self._servers.get(server_id)
        if not s:
            return None
        tools_count = len(mcp_tool_registry.list_tools(server_id))
        return MCPServerResponse(
            id=server_id,
            name=s["name"],
            description=s["description"],
            transport_type=MCPTransportType(s["transport_type"]),
            status=MCPServerStatus(s["status"]),
            config=s["config"],
            tools_count=tools_count,
            created_at=s["created_at"],
            updated_at=s["updated_at"],
        )

    async def execute_tool(
        self,
        request: MCPToolExecuteRequest,
        user_id: str = "default_user",
    ) -> MCPToolExecuteResponse:
        """Unified tool execution entry point."""
        # Find tool definition
        identifier = f"{request.server_id}:{request.tool_name}" if request.server_id else request.tool_name
        tool_def = mcp_tool_registry.get_tool(identifier)

        server_id = request.server_id or (tool_def.server_id if tool_def else None)
        tool_name = request.tool_name

        if not server_id:
            return MCPToolExecuteResponse(
                tool_name=tool_name,
                server_id="unknown",
                status="FAILED",
                error=f"MCP Tool '{tool_name}' not found or no server specified.",
            )

        # Get server connection
        conn = mcp_client_manager.get_connection(server_id)
        if not conn or conn.status != MCPServerStatus.CONNECTED:
            # Try auto-connecting
            if server_id in self._servers:
                await self.connect_server(server_id)
                conn = mcp_client_manager.get_connection(server_id)

        async def runner(t_name: str, args: Dict[str, Any]):
            if not conn:
                raise RuntimeError(f"Server '{server_id}' is not connected")
            return await conn.call_tool(t_name, args)

        return await mcp_executor.execute(
            server_id=server_id,
            tool_name=tool_name,
            arguments=request.arguments,
            user_id=user_id,
            approval_id=request.approval_id,
            runner_fn=runner,
        )

    def get_health_summary(self) -> MCPHealthSummary:
        """Generate high-level MCP health status."""
        servers = self.list_servers()
        total_servers = len(servers)
        active_servers = sum(1 for s in servers if s.status == MCPServerStatus.CONNECTED)
        total_tools = len(mcp_tool_registry.list_tools())
        pending_approvals = len(approval_queue.list_requests(status=None))

        return MCPHealthSummary(
            total_servers=total_servers,
            active_servers=active_servers,
            connected_servers=active_servers,
            total_tools=total_tools,
            pending_approvals=pending_approvals,
            recent_executions_count=len(mcp_executor._logs),
            default_policy="DENY",
            status="healthy" if active_servers > 0 else "degraded",
        )


# Global singleton manager
mcp_manager = MCPManager()
