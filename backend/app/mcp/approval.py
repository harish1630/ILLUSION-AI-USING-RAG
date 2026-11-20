"""Human Approval Queue for MCP tool execution.

Handles APPROVAL_REQUIRED tools:
- Creates pending approval requests
- Allows humans to review, approve, or reject
- Tracks audit trail with timestamp and reviewer
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging
try:
    from app.mcp.schemas import ApprovalStatus
except ImportError:
    from backend.app.mcp.schemas import ApprovalStatus

logger = logging.getLogger(__name__)


class MCPApprovalQueue:
    """In-memory and persistent approval request queue."""

    def __init__(self):
        # Key: approval_id -> dict
        self._approvals: Dict[str, Dict[str, Any]] = {}

    def create_request(
        self,
        user_id: str,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new pending approval request."""
        approval_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        record = {
            "id": approval_id,
            "user_id": user_id,
            "server_id": server_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "status": ApprovalStatus.PENDING.value,
            "created_at": created_at,
            "reviewed_at": None,
            "reviewer_id": None,
        }
        self._approvals[approval_id] = record
        logger.info(f"Created MCP approval request {approval_id} for {tool_name} on {server_id}")
        return record

    def get_request(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an approval request by ID."""
        return self._approvals.get(approval_id)

    def list_requests(
        self,
        user_id: Optional[str] = None,
        status: Optional[ApprovalStatus] = None,
    ) -> List[Dict[str, Any]]:
        """List requests optionally filtered by user or status."""
        results = []
        for req in self._approvals.values():
            if user_id and req["user_id"] != user_id:
                continue
            if status and req["status"] != status.value:
                continue
            results.append(req)
        # Sort newest first
        results.sort(key=lambda x: x["created_at"], reverse=True)
        return results

    def resolve_request(
        self,
        approval_id: str,
        approved: bool,
        reviewer_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Approve or reject a pending request."""
        req = self._approvals.get(approval_id)
        if not req:
            return None
        if req["status"] != ApprovalStatus.PENDING.value:
            logger.warning(f"Approval request {approval_id} already in status {req['status']}")
            return req

        now = datetime.now(timezone.utc).isoformat()
        req["status"] = ApprovalStatus.APPROVED.value if approved else ApprovalStatus.REJECTED.value
        req["reviewed_at"] = now
        req["reviewer_id"] = reviewer_id or req["user_id"]
        logger.info(f"Approval {approval_id} resolved: {req['status']}")
        return req


# Global singleton instance
approval_queue = MCPApprovalQueue()
