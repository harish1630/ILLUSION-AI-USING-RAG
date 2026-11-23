"""Unit and Integration Tests for Illusion AI Plugin Marketplace."""

import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.plugins import (
    plugin_manager,
    PermissionLevel,
    ExecutionStatus,
)
from app.tools.router import ToolRouter, ToolSelectionMode


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_plugins():
    # Setup mock connections for testing
    plugin_manager.connect_user_plugin(
        user_id="test_marketplace_user",
        plugin_id="gmail",
        raw_credentials={
            "access_token": "mock_gmail_access_token_12345",
            "account_id": "google_12345",
            "account_email": "testfounder@illusion.ai",
            "account_username": "testfounder",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"],
        },
    )
    plugin_manager.connect_user_plugin(
        user_id="test_marketplace_user",
        plugin_id="github",
        raw_credentials={
            "access_token": "mock_github_access_token_67890",
            "account_id": "gh_67890",
            "account_email": "dev@illusion.ai",
            "account_username": "illusion-test-dev",
            "scopes": ["repo", "read:user"],
        },
    )


# ---------------------------------------------------------------------------
# 1. Plugin Catalog & Integrations
# ---------------------------------------------------------------------------

def test_api_list_catalog_plugins(client):
    resp = client.get("/api/marketplace/plugins")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 6
    plugin_ids = [p["id"] for p in data]
    assert "gmail" in plugin_ids
    assert "github" in plugin_ids
    assert "custom_mcp" in plugin_ids


def test_api_list_user_integrations(client):
    resp = client.get("/api/marketplace/integrations")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_api_connect_oauth_url(client):
    resp = client.post("/api/marketplace/connect/gmail")
    assert resp.status_code == 200
    data = resp.json()
    assert "authorization_url" in data
    assert "accounts.google.com" in data["authorization_url"]
    assert "state" in data
    assert data["plugin_id"] == "gmail"


def test_api_connect_direct_mock(client):
    payload = {
        "plugin_id": "gmail",
        "access_token": "mock_test_token_direct",
        "account_email": "direct_connect@example.com",
        "account_username": "direct_user",
    }
    resp = client.post("/api/marketplace/connect-direct", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "connected"


# ---------------------------------------------------------------------------
# 2. Tool Permissions & Default-Deny Policy
# ---------------------------------------------------------------------------

def test_api_get_permissions(client):
    resp = client.get("/api/marketplace/permissions/gmail")
    assert resp.status_code == 200
    perms = resp.json()
    tool_names = [p["tool_name"] for p in perms]
    assert "gmail_search_emails" in tool_names
    assert "gmail_send_email" in tool_names

    # Verify send email defaults to APPROVAL_REQUIRED
    send_perm = next(p for p in perms if p["tool_name"] == "gmail_send_email")
    assert send_perm["is_sensitive"] is True
    assert send_perm["default_permission"] == "APPROVAL_REQUIRED"


def test_api_update_permission(client):
    payload = {
        "plugin_id": "gmail",
        "tool_name": "gmail_search_emails",
        "permission_level": "DENY",
    }
    resp = client.post("/api/marketplace/permissions", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "updated"
    assert data["permission_level"] == "DENY"

    # Reset back to ALLOW
    payload["permission_level"] = "ALLOW"
    client.post("/api/marketplace/permissions", json=payload)


# ---------------------------------------------------------------------------
# 3. Tool Execution & Human Approvals
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_gmail_search_emails():
    res = await plugin_manager.execute_tool(
        user_id="test_marketplace_user",
        plugin_id="gmail",
        tool_name="gmail_search_emails",
        arguments={"query": "TN MSME Subsidy", "max_results": 2},
    )
    assert res.status == ExecutionStatus.SUCCESS
    assert res.result["count"] >= 1
    assert "emails" in res.result


@pytest.mark.asyncio
async def test_execute_gmail_send_requires_approval():
    # Sensitive action without approval token must yield APPROVAL_REQUIRED
    res = await plugin_manager.execute_tool(
        user_id="test_marketplace_user",
        plugin_id="gmail",
        tool_name="gmail_send_email",
        arguments={"to": "investor@example.com", "subject": "Pitch Deck", "body": "See attached"},
    )
    assert res.status == ExecutionStatus.APPROVAL_REQUIRED
    assert res.approval_id is not None

    # Approve request
    appr_id = res.approval_id
    success = plugin_manager.approve_request("test_marketplace_user", appr_id)
    assert success is True

    # Re-execute with approved token
    res_approved = await plugin_manager.execute_tool(
        user_id="test_marketplace_user",
        plugin_id="gmail",
        tool_name="gmail_send_email",
        arguments={"to": "investor@example.com", "subject": "Pitch Deck", "body": "See attached"},
        approval_token=appr_id,
    )
    assert res_approved.status == ExecutionStatus.SUCCESS
    assert res_approved.result["status"] == "sent"


@pytest.mark.asyncio
async def test_execute_github_tools():
    # List repos
    res_repos = await plugin_manager.execute_tool(
        user_id="test_marketplace_user",
        plugin_id="github",
        tool_name="github_list_repositories",
        arguments={},
    )
    assert res_repos.status == ExecutionStatus.SUCCESS
    assert len(res_repos.result) >= 1

    # List issues
    res_issues = await plugin_manager.execute_tool(
        user_id="test_marketplace_user",
        plugin_id="github",
        tool_name="github_list_issues",
        arguments={"repo_name": "founder/illusion-ai"},
    )
    assert res_issues.status == ExecutionStatus.SUCCESS
    assert len(res_issues.result) >= 1


# ---------------------------------------------------------------------------
# 4. Audit Logs
# ---------------------------------------------------------------------------

def test_api_audit_logs(client):
    resp = client.get("/api/marketplace/audit-logs")
    assert resp.status_code == 200
    logs = resp.json()
    assert isinstance(logs, list)
    assert len(logs) >= 1


# ---------------------------------------------------------------------------
# 5. AI Router Integration with Marketplace Tools
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_router_detects_gmail_intent():
    planned = await ToolRouter.route(
        prompt="Search email for TN MSME Subsidy approval notice in my inbox",
        mode=ToolSelectionMode.AUTO,
    )
    tool_names = [p.tool_name for p in planned]
    assert "gmail_search_emails" in tool_names


@pytest.mark.asyncio
async def test_router_detects_github_issue_intent():
    planned = await ToolRouter.route(
        prompt="Create issue in my repository for login token refresh bug",
        mode=ToolSelectionMode.AUTO,
    )
    tool_names = [p.tool_name for p in planned]
    assert "github_create_issue" in tool_names
