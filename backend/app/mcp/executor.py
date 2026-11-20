"""Sandboxed MCP Tool Executor.

Enforces:
- Permission checking (ALLOW, APPROVAL_REQUIRED, DENY)
- 15-second execution timeout
- Sandboxed error handling and response formatting
- Audit logging of all executions
"""

import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging

try:
    from app.mcp.schemas import (
        PermissionLevel,
        ApprovalStatus,
        ExecutionStatus,
        MCPToolExecuteResponse,
    )
    from app.mcp.permissions import permission_manager
    from app.mcp.approval import approval_queue
except ImportError:
    from backend.app.mcp.schemas import (
        PermissionLevel,
        ApprovalStatus,
        ExecutionStatus,
        MCPToolExecuteResponse,
    )
    from backend.app.mcp.permissions import permission_manager
    from backend.app.mcp.approval import approval_queue

logger = logging.getLogger(__name__)


class MCPExecutor:
    """Safely executes MCP tools under policy and timeout constraints."""

    def __init__(self):
        # Execution audit log history
        self._logs: List[Dict[str, Any]] = []

    def log_execution(
        self,
        user_id: str,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        status: ExecutionStatus,
        result: Optional[Any] = None,
        error_message: Optional[str] = None,
        duration_ms: float = 0.0,
    ) -> Dict[str, Any]:
        """Record an execution in the audit log."""
        log_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "server_id": server_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "status": status.value,
            "result": result,
            "error_message": error_message,
            "duration_ms": duration_ms,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        self._logs.append(log_entry)
        # Keep last 500 logs in memory
        if len(self._logs) > 500:
            self._logs.pop(0)
        return log_entry

    def list_logs(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent execution logs."""
        filtered = [l for l in self._logs if user_id is None or l["user_id"] == user_id]
        filtered.sort(key=lambda x: x["executed_at"], reverse=True)
        return filtered[:limit]

    async def execute(
        self,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        user_id: str = "default_user",
        approval_id: Optional[str] = None,
        runner_fn: Optional[Any] = None,
        timeout_seconds: float = 15.0,
    ) -> MCPToolExecuteResponse:
        """Execute an MCP tool subject to permissions, approvals, and timeout."""
        start_time = time.time()

        # Step 1: Check Permissions
        perm = permission_manager.get_permission(user_id, server_id, tool_name)

        if perm == PermissionLevel.DENY:
            duration_ms = (time.time() - start_time) * 1000
            err = f"Execution denied: Tool '{tool_name}' on server '{server_id}' is blocked by policy."
            self.log_execution(
                user_id=user_id,
                server_id=server_id,
                tool_name=tool_name,
                arguments=arguments,
                status=ExecutionStatus.FAILED,
                error_message=err,
                duration_ms=duration_ms,
            )
            return MCPToolExecuteResponse(
                tool_name=tool_name,
                server_id=server_id,
                status=ExecutionStatus.FAILED,
                error=err,
                execution_time_ms=duration_ms,
            )

        if perm == PermissionLevel.APPROVAL_REQUIRED:
            # Check if an approved approval_id was provided
            if approval_id:
                req = approval_queue.get_request(approval_id)
                if not req or req["status"] != ApprovalStatus.APPROVED.value:
                    duration_ms = (time.time() - start_time) * 1000
                    err = f"Approval required: Provided approval token {approval_id} is not approved."
                    return MCPToolExecuteResponse(
                        tool_name=tool_name,
                        server_id=server_id,
                        status=ExecutionStatus.DENIED,
                        error=err,
                        execution_time_ms=duration_ms,
                    )
            else:
                # Create pending approval request and return PENDING_APPROVAL
                req = approval_queue.create_request(
                    user_id=user_id,
                    server_id=server_id,
                    tool_name=tool_name,
                    arguments=arguments,
                )
                duration_ms = (time.time() - start_time) * 1000
                return MCPToolExecuteResponse(
                    tool_name=tool_name,
                    server_id=server_id,
                    status=ExecutionStatus.PENDING_APPROVAL,
                    approval_id=req["id"],
                    result={
                        "message": f"Action requires human approval for tool '{tool_name}'.",
                        "approval_id": req["id"],
                        "arguments": arguments,
                    },
                    execution_time_ms=duration_ms,
                )

        # Step 2: Tool Runner Invocation under Timeout
        if runner_fn is None:
            duration_ms = (time.time() - start_time) * 1000
            err = f"No execution runner configured for server '{server_id}'."
            return MCPToolExecuteResponse(
                tool_name=tool_name,
                server_id=server_id,
                status=ExecutionStatus.FAILED,
                error=err,
                execution_time_ms=duration_ms,
            )

        try:
            # Enforce 15s timeout
            result = await asyncio.wait_for(runner_fn(tool_name, arguments), timeout=timeout_seconds)
            duration_ms = (time.time() - start_time) * 1000

            self.log_execution(
                user_id=user_id,
                server_id=server_id,
                tool_name=tool_name,
                arguments=arguments,
                status=ExecutionStatus.SUCCESS,
                result=result,
                duration_ms=duration_ms,
            )

            return MCPToolExecuteResponse(
                tool_name=tool_name,
                server_id=server_id,
                status=ExecutionStatus.SUCCESS,
                result=result,
                execution_time_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            err = f"Execution timed out after {timeout_seconds} seconds."
            self.log_execution(
                user_id=user_id,
                server_id=server_id,
                tool_name=tool_name,
                arguments=arguments,
                status=ExecutionStatus.TIMEOUT,
                error_message=err,
                duration_ms=duration_ms,
            )
            return MCPToolExecuteResponse(
                tool_name=tool_name,
                server_id=server_id,
                status=ExecutionStatus.TIMEOUT,
                error=err,
                execution_time_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            err = f"Tool execution failed: {str(e)}"
            self.log_execution(
                user_id=user_id,
                server_id=server_id,
                tool_name=tool_name,
                arguments=arguments,
                status=ExecutionStatus.FAILED,
                error_message=err,
                duration_ms=duration_ms,
            )
            return MCPToolExecuteResponse(
                tool_name=tool_name,
                server_id=server_id,
                status=ExecutionStatus.FAILED,
                error=err,
                execution_time_ms=duration_ms,
            )


# Global singleton executor
mcp_executor = MCPExecutor()
