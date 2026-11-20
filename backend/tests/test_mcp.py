"""Unit and integration tests for Model Context Protocol (MCP) in Illusion AI."""

import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app

from app.mcp import (
    mcp_manager,
    mcp_tool_registry,
    permission_manager,
    approval_queue,
    mcp_executor,
    MCPToolExecuteRequest,
    PermissionLevel,
    ApprovalStatus,
    ExecutionStatus,
)
from app.mcp_servers.custom_server import (
    get_project_info,
    list_project_modules,
    calculate,
    get_system_status,
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_mcp():
    asyncio.run(mcp_manager.initialize())


# ---------------------------------------------------------------------------
# 1. Custom MCP Server (illusion_custom) Tool Tests
# ---------------------------------------------------------------------------

def test_custom_server_get_project_info():
    info = get_project_info()
    assert info["project_name"] == "Illusion AI"
    assert info["version"] == "2.0.0"
    assert "MCP (Model Context Protocol)" in info["architecture"]["protocols"]
    assert info["status"] == "operational"


def test_custom_server_list_project_modules():
    modules = list_project_modules()
    assert "/api/mcp/servers" in modules["backend_modules"]["api_routes"]
    assert "/api/github/url" in modules["backend_modules"]["api_routes"]
    assert "MCPClientManager" in modules["backend_modules"]["mcp_engine"]
    assert "/mcp" in modules["frontend_modules"]["pages"]


def test_custom_server_calculate_safe_math():
    # Basic math
    res = calculate("125 * 4 + 25")
    assert res["status"] == "success"
    assert res["result"] == 525.0

    # Complex expression with parentheses and exponents
    res2 = calculate("(10 + 5) * 2 - 2^3")
    assert res2["status"] == "success"
    assert res2["result"] == 22.0

    # Division by zero handled safely without crash
    res_zero = calculate("100 / 0")
    assert res_zero["status"] == "error"
    assert "Division by zero" in res_zero["error"]


def test_custom_server_get_system_status_no_secrets():
    status = get_system_status()
    assert status["status"] == "healthy"
    assert status["security"]["secrets_exposed"] is False
    assert status["security"]["mcp_default_policy"] == "DENY"
    # Verify no raw passwords, keys, or tokens are returned
    status_str = str(status).lower()
    assert "gocspx" not in status_str
    assert "sk-" not in status_str


# ---------------------------------------------------------------------------
# 2. Permissions System Tests (Default DENY, ALLOW, APPROVAL_REQUIRED)
# ---------------------------------------------------------------------------

def test_permission_default_deny():
    # Unknown tool or server must be DENY by default
    perm = permission_manager.get_permission("test_user", "unknown_server", "dangerous_tool")
    assert perm == PermissionLevel.DENY


def test_permission_custom_rule():
    permission_manager.set_permission("user_123", "ext_server", "format_disk", PermissionLevel.APPROVAL_REQUIRED)
    assert permission_manager.get_permission("user_123", "ext_server", "format_disk") == PermissionLevel.APPROVAL_REQUIRED
    # Another user still denied
    assert permission_manager.get_permission("user_456", "ext_server", "format_disk") == PermissionLevel.DENY


# ---------------------------------------------------------------------------
# 3. Approval Workflow Tests
# ---------------------------------------------------------------------------

def test_approval_request_lifecycle():
    # Create request
    req = approval_queue.create_request(
        user_id="user_test",
        server_id="ext_server",
        tool_name="delete_database",
        arguments={"db": "demo"},
    )
    req_id = req["id"]
    assert req["status"] == ApprovalStatus.PENDING.value

    # List pending
    pending = approval_queue.list_requests(status=ApprovalStatus.PENDING)
    assert any(r["id"] == req_id for r in pending)

    # Approve
    approved = approval_queue.resolve_request(req_id, approved=True, reviewer_id="admin_user")
    assert approved["status"] == ApprovalStatus.APPROVED.value
    assert approved["reviewer_id"] == "admin_user"


# ---------------------------------------------------------------------------
# 4. MCP Manager Tool Execution Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_manager_execute_allowed_tool():
    req = MCPToolExecuteRequest(
        server_id="illusion_custom",
        tool_name="calculate",
        arguments={"expression": "50 * 2"},
    )
    res = await mcp_manager.execute_tool(req, user_id="test_user")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.result["result"] == 100.0


@pytest.mark.asyncio
async def test_mcp_manager_execute_denied_tool():
    # Set explicit DENY
    permission_manager.set_permission("test_user", "illusion_custom", "restricted_tool", PermissionLevel.DENY)
    req = MCPToolExecuteRequest(
        server_id="illusion_custom",
        tool_name="restricted_tool",
        arguments={},
    )
    res = await mcp_manager.execute_tool(req, user_id="test_user")
    assert res.status == ExecutionStatus.FAILED
    assert "Execution denied" in res.error


# ---------------------------------------------------------------------------
# 5. MCP FastAPI Endpoints Tests
# ---------------------------------------------------------------------------

def test_api_mcp_health(client):
    resp = client.get("/api/mcp/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["default_policy"] == "DENY"
    assert data["active_servers"] >= 1


def test_api_mcp_servers(client):
    resp = client.get("/api/mcp/servers")
    assert resp.status_code == 200
    servers = resp.json()
    assert any(s["id"] == "illusion_custom" for s in servers)


def test_api_mcp_tools(client):
    resp = client.get("/api/mcp/tools")
    assert resp.status_code == 200
    tools = resp.json()
    tool_names = [t["tool_name"] for t in tools]
    assert "calculate" in tool_names
    assert "get_project_info" in tool_names


def test_api_mcp_execute_tool(client):
    payload = {
        "server_id": "illusion_custom",
        "tool_name": "calculate",
        "arguments": {"expression": "25 * 4"},
    }
    resp = client.post("/api/mcp/tools/execute", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["result"]["result"] == 100.0
