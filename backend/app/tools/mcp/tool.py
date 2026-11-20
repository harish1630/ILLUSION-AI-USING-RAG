"""MCP Bridge Tool connecting dynamic MCP servers to the internal ToolRegistry."""

from typing import Dict, Any, Optional
from app.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult
try:
    from app.mcp import mcp_manager, MCPToolExecuteRequest
except ImportError:
    from backend.app.mcp import mcp_manager, MCPToolExecuteRequest


class MCPBridgeTool(BaseTool):
    """Executes arbitrary MCP tools discovered dynamically on connected MCP servers."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="mcp_execute",
            display_name="Model Context Protocol Executor",
            description="Execute dynamic tools from connected MCP servers (such as custom diagnostics or external MCP tools).",
            parameters=[
                ToolParameter(name="server_id", type="string", description="MCP Server identifier (e.g. 'illusion_custom')", required=True),
                ToolParameter(name="tool_name", type="string", description="Tool name to execute on the server", required=True),
                ToolParameter(name="arguments", type="object", description="Tool input arguments dictionary", required=False, default={}),
                ToolParameter(name="approval_id", type="string", description="Optional approval ID if previously requested", required=False, default=None),
            ],
            category="mcp",
            requires_auth=False,
        )

    async def execute(
        self,
        server_id: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        approval_id: Optional[str] = None,
        user_id: str = "default_user",
        **kwargs,
    ) -> ToolResult:
        try:
            req = MCPToolExecuteRequest(
                server_id=server_id,
                tool_name=tool_name,
                arguments=arguments or {},
                approval_id=approval_id,
            )
            res = await mcp_manager.execute_tool(req, user_id=user_id)
            if res.status == "SUCCESS":
                return ToolResult(tool_name=f"{server_id}:{tool_name}", success=True, data=res.result)
            elif res.status == "PENDING_APPROVAL":
                return ToolResult(
                    tool_name=f"{server_id}:{tool_name}",
                    success=False,
                    error="Action requires human approval before proceeding.",
                    metadata={"approval_id": res.approval_id, "status": "PENDING_APPROVAL"},
                )
            else:
                return ToolResult(tool_name=f"{server_id}:{tool_name}", success=False, error=res.error)
        except Exception as e:
            return ToolResult(tool_name=f"{server_id}:{tool_name}", success=False, error=str(e))
