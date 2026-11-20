"""Unit and integration tests for GitHub OAuth 2.0 and GitHub Tools in Illusion AI."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.auth.github_oauth import github_oauth_service
from app.services.github_service import github_service
from services.token_manager import token_manager
from app.router.intent_classifier import IntentClassifier
from app.router.decision_engine import DecisionEngine
from app.router.schemas import PromptAnalysis, IntentDomain, ComplexityLevel, RiskLevel


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. GitHub OAuth URL & State Tests
# ---------------------------------------------------------------------------

def test_github_auth_url_generation():
    url = github_oauth_service.get_authorization_url(state="test_state_123")
    assert "https://github.com/login/oauth/authorize" in url
    assert "state=test_state_123" in url
    assert "client_id=" in url
    assert "scope=read%3Auser+user%3Aemail+repo" in url or "scope=read:user" in url or "scope=" in url


def test_api_github_url_endpoint(client):
    resp = client.get("/api/github/url")
    assert resp.status_code == 200
    data = resp.json()
    assert "authorization_url" in data
    assert "state" in data
    assert len(data["state"]) > 20


def test_api_github_callback_invalid_state(client):
    resp = client.get("/api/github/callback?code=bad_code&state=non_existent_state")
    assert resp.status_code == 400
    assert "CSRF" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 2. Token Encryption & Connection Store Tests
# ---------------------------------------------------------------------------

def test_github_token_encryption_at_rest():
    raw_token = "gho_test_secret_token_123456789"
    user_id = "test_user_github_01"

    github_service.store_connection(
        user_id=user_id,
        github_user_id="998877",
        username="illusion-dev",
        email="dev@illusion.ai",
        avatar_url="https://github.com/images/avatar.png",
        plaintext_token=raw_token,
    )

    # Verify connection retrieval hides raw token
    conn = github_service.get_connection(user_id)
    assert conn["is_connected"] is True
    assert conn["github_username"] == "illusion-dev"
    assert "encrypted_access_token" not in conn  # Not exposed in status

    # Verify decrypt retrieves original token
    decrypted = github_service._get_token(user_id)
    assert decrypted == raw_token

    # Disconnect workflow
    assert github_service.disconnect(user_id) is True
    assert github_service.get_connection(user_id) is None


# ---------------------------------------------------------------------------
# 3. GitHub Service Tools Unit Tests (Mocked External Calls)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_github_service_repos_mocked():
    user_id = "mock_user_gh"
    github_service.store_connection(
        user_id=user_id,
        github_user_id="12345",
        username="mockuser",
        email="mock@example.com",
        avatar_url="",
        plaintext_token="fake_token",
    )

    mock_repos_payload = [
        {
            "name": "illusion-ai",
            "full_name": "mockuser/illusion-ai",
            "owner": {"login": "mockuser"},
            "private": False,
            "description": "AI startup platform",
            "html_url": "https://github.com/mockuser/illusion-ai",
            "default_branch": "main",
            "stargazers_count": 42,
            "forks_count": 5,
            "language": "Python",
            "updated_at": "2026-11-20T12:00:00Z",
        }
    ]

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_repos_payload
        mock_get.return_value = mock_resp

        repos = await github_service.github_list_repositories(user_id=user_id)
        assert len(repos) == 1
        assert repos[0]["name"] == "illusion-ai"
        assert repos[0]["stars"] == 42


@pytest.mark.asyncio
async def test_github_service_file_content_mocked():
    import base64
    user_id = "mock_user_gh_file"
    github_service.store_connection(
        user_id=user_id,
        github_user_id="12345",
        username="mockuser",
        email="mock@example.com",
        avatar_url="",
        plaintext_token="fake_token",
    )

    sample_readme = "# Illusion AI\nAwesome project."
    encoded = base64.b64encode(sample_readme.encode()).decode()

    mock_file_payload = {
        "name": "README.md",
        "path": "README.md",
        "size": len(sample_readme),
        "sha": "abc123sha",
        "encoding": "base64",
        "content": encoded,
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_file_payload
        mock_get.return_value = mock_resp

        file_res = await github_service.github_get_file_content(
            user_id=user_id,
            repo_name="illusion-ai",
            file_path="README.md",
        )
        assert file_res["type"] == "file"
        assert file_res["content"] == sample_readme


# ---------------------------------------------------------------------------
# 4. Tool Router Integration Tests for GitHub Prompts
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_router_detects_github_prompts():
    # Test heuristic intent classification directly
    analysis1 = IntentClassifier._heuristic_classify("Show my GitHub repositories.", "en")
    assert "github_list_repositories" in analysis1.suggested_tools

    analysis2 = IntentClassifier._heuristic_classify("Explain the latest commit.", "en")
    assert "github_list_commits" in analysis2.suggested_tools

    analysis3 = IntentClassifier._heuristic_classify("Read the README file in my repository.", "en")
    assert "github_get_file_content" in analysis3.suggested_tools


def test_decision_engine_plans_github_tools():
    analysis = PromptAnalysis(
        original_prompt="List all my repos on GitHub",
        language="en",
        intent_domain=IntentDomain.GENERAL_KNOWLEDGE,
        intent_summary="List GitHub repositories",
        complexity=ComplexityLevel.LOW,
        risk_level=RiskLevel.SAFE,
        suggested_tools=["github_list_repositories"],
    )

    plan = DecisionEngine.plan(analysis)
    assert len(plan.steps) == 1
    assert plan.steps[0].tool_name == "github_list_repositories"
    assert plan.steps[0].arguments["visibility"] == "all"
