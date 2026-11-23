"""GitHub Integration Plugin for Illusion AI."""

import secrets
import base64
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlencode
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.plugins.base import BasePlugin
from app.plugins.schemas import PluginToolDefinition, PermissionLevel
from app.services.github_service import GitHubService, GITHUB_API_BASE

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"

GITHUB_SCOPES = ["repo", "read:user", "user:email"]


class GitHubPlugin(BasePlugin):
    """GitHub marketplace plugin for repository analysis, code inspection, and issue tracking."""

    def __init__(self, service: Optional[GitHubService] = None):
        super().__init__(
            plugin_id="github",
            name="github",
            display_name="GitHub",
            description="Analyze repositories, browse commits & branches, view issues, and create issue tickets directly from chat.",
            category="developer",
            icon="Github",
            auth_type="oauth2",
            scopes=GITHUB_SCOPES,
            features=[
                "List and inspect repositories",
                "Read file contents & tree",
                "View & create issue tickets",
                "Review recent commits & branches",
            ],
        )
        self.service = service or GitHubService()

    def get_tools(self) -> List[PluginToolDefinition]:
        return [
            PluginToolDefinition(
                tool_name="github_list_repositories",
                qualified_name="github:github_list_repositories",
                description="List repositories accessible by user on GitHub (public and authorized private)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "visibility": {"type": "string", "enum": ["all", "public", "private"], "default": "all"},
                        "limit": {"type": "integer", "default": 20},
                    },
                },
                is_sensitive=False,
                default_permission=PermissionLevel.ALLOW,
            ),
            PluginToolDefinition(
                tool_name="github_get_repository",
                qualified_name="github:github_get_repository",
                description="Get detailed metadata for a specific repository (e.g. 'owner/repo')",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_name": {"type": "string", "description": "Full repository name e.g. 'owner/repo' or 'repo'"},
                    },
                    "required": ["repo_name"],
                },
                is_sensitive=False,
                default_permission=PermissionLevel.ALLOW,
            ),
            PluginToolDefinition(
                tool_name="github_get_file_content",
                qualified_name="github:github_get_file_content",
                description="Retrieve decoded file contents from a repository at a given path",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_name": {"type": "string", "description": "Full repository name 'owner/repo'"},
                        "path": {"type": "string", "description": "Path to file inside repo e.g. 'README.md'"},
                        "branch": {"type": "string", "description": "Branch name (default 'main')", "default": "main"},
                    },
                    "required": ["repo_name", "path"],
                },
                is_sensitive=False,
                default_permission=PermissionLevel.ALLOW,
            ),
            PluginToolDefinition(
                tool_name="github_list_branches",
                qualified_name="github:github_list_branches",
                description="List all Git branches for a repository",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_name": {"type": "string", "description": "Repository 'owner/repo'"},
                    },
                    "required": ["repo_name"],
                },
                is_sensitive=False,
                default_permission=PermissionLevel.ALLOW,
            ),
            PluginToolDefinition(
                tool_name="github_list_commits",
                qualified_name="github:github_list_commits",
                description="List recent commits for a repository with author and commit messages",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_name": {"type": "string", "description": "Repository 'owner/repo'"},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": ["repo_name"],
                },
                is_sensitive=False,
                default_permission=PermissionLevel.ALLOW,
            ),
            PluginToolDefinition(
                tool_name="github_search_code",
                qualified_name="github:github_search_code",
                description="Search code inside a repository for keywords, classes, or function names",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_name": {"type": "string", "description": "Repository 'owner/repo'"},
                        "query": {"type": "string", "description": "Search keyword or symbol"},
                    },
                    "required": ["repo_name", "query"],
                },
                is_sensitive=False,
                default_permission=PermissionLevel.ALLOW,
            ),
            PluginToolDefinition(
                tool_name="github_list_issues",
                qualified_name="github:github_list_issues",
                description="List open and closed issue tickets in a repository",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_name": {"type": "string", "description": "Repository 'owner/repo'"},
                        "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"},
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": ["repo_name"],
                },
                is_sensitive=False,
                default_permission=PermissionLevel.ALLOW,
            ),
            PluginToolDefinition(
                tool_name="github_create_issue",
                qualified_name="github:github_create_issue",
                description="Create a new issue ticket in a repository. SENSITIVE: Requires human confirmation.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "repo_name": {"type": "string", "description": "Repository 'owner/repo'"},
                        "title": {"type": "string", "description": "Issue title"},
                        "body": {"type": "string", "description": "Issue description / body markdown"},
                        "labels": {"type": "array", "items": {"type": "string"}, "description": "Optional labels"},
                    },
                    "required": ["repo_name", "title", "body"],
                },
                is_sensitive=True,
                default_permission=PermissionLevel.APPROVAL_REQUIRED,
            ),
        ]

    def get_auth_url(self, user_id: str, redirect_uri: str) -> Tuple[str, str]:
        client_id = settings.GITHUB_CLIENT_ID
        state = f"github_{secrets.token_urlsafe(24)}"

        # If running in development without real GitHub OAuth credentials,
        # redirect directly to the callback endpoint with a mock code so local demo/testing works seamlessly
        if not client_id or client_id.startswith("github_mock") or client_id == "your_github_client_id_here":
            dev_url = f"{redirect_uri}?code=mock_github_code_{secrets.token_hex(8)}&state={state}&user_id={user_id}"
            return dev_url, state

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
        }
        url = f"{GITHUB_AUTH_URL}?{urlencode(params)}"
        return url, state

    async def exchange_code(self, code: str, redirect_uri: str, state: Optional[str] = None) -> Dict[str, Any]:
        client_id = settings.GITHUB_CLIENT_ID
        client_secret = settings.GITHUB_CLIENT_SECRET

        if not client_id or not client_secret or client_id.startswith("github_mock") or code.startswith("mock_"):
            logger.info("Using mock GitHub token exchange for test/development")
            return {
                "access_token": f"mock_github_access_{secrets.token_hex(16)}",
                "refresh_token": None,
                "expires_at": None,
                "account_id": "gh_12345678",
                "account_email": "developer@illusion.ai",
                "account_username": "illusion-dev",
                "avatar_url": "https://avatars.githubusercontent.com/u/9919?v=4",
                "scopes": self.scopes,
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.post(
                GITHUB_TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )

            if token_resp.status_code != 200:
                raise ValueError(f"GitHub token exchange failed: {token_resp.text}")

            token_data = token_resp.json()
            if "error" in token_data:
                raise ValueError(f"GitHub OAuth error: {token_data.get('error_description')}")

            access_token = token_data.get("access_token")

            # Fetch user profile
            profile_resp = await client.get(
                f"{GITHUB_API_BASE}/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "Illusion-AI",
                },
            )
            profile = profile_resp.json() if profile_resp.status_code == 200 else {}

            return {
                "access_token": access_token,
                "refresh_token": None,
                "expires_at": None,
                "account_id": str(profile.get("id", "")),
                "account_email": profile.get("email"),
                "account_username": profile.get("login", "github_user"),
                "avatar_url": profile.get("avatar_url"),
                "scopes": self.scopes,
            }

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        credentials: Dict[str, Any],
    ) -> Any:
        access_token = credentials.get("access_token")
        if not access_token:
            raise ValueError("GitHub access token missing or invalid")

        if access_token.startswith("mock_"):
            return self._execute_mock(tool_name, arguments)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "Illusion-AI",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            if tool_name == "github_list_repositories":
                resp = await client.get(f"{GITHUB_API_BASE}/user/repos", headers=headers, params={"per_page": 20})
                if resp.status_code != 200:
                    raise RuntimeError(f"GitHub list repos failed: {resp.text}")
                return [
                    {
                        "name": r.get("name"),
                        "full_name": r.get("full_name"),
                        "description": r.get("description"),
                        "private": r.get("private"),
                        "html_url": r.get("html_url"),
                        "language": r.get("language"),
                        "stars": r.get("stargazers_count"),
                    }
                    for r in resp.json()
                ]

            elif tool_name == "github_get_repository":
                repo = arguments.get("repo_name", "")
                resp = await client.get(f"{GITHUB_API_BASE}/repos/{repo}", headers=headers)
                if resp.status_code != 200:
                    raise RuntimeError(f"GitHub get repo failed: {resp.text}")
                r = resp.json()
                return {
                    "full_name": r.get("full_name"),
                    "description": r.get("description"),
                    "default_branch": r.get("default_branch"),
                    "open_issues_count": r.get("open_issues_count"),
                    "forks_count": r.get("forks_count"),
                    "stargazers_count": r.get("stargazers_count"),
                    "updated_at": r.get("updated_at"),
                }

            elif tool_name == "github_get_file_content":
                repo = arguments.get("repo_name", "")
                path = arguments.get("path", "")
                branch = arguments.get("branch", "main")
                resp = await client.get(
                    f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}",
                    headers=headers,
                    params={"ref": branch},
                )
                if resp.status_code != 200:
                    raise RuntimeError(f"GitHub file read failed: {resp.text}")
                data = resp.json()
                raw_b64 = data.get("content", "")
                decoded = base64.b64decode(raw_b64).decode("utf-8", errors="replace")
                return {
                    "repo_name": repo,
                    "path": path,
                    "branch": branch,
                    "size_bytes": data.get("size", 0),
                    "content": decoded,
                }

            elif tool_name == "github_list_branches":
                repo = arguments.get("repo_name", "")
                resp = await client.get(f"{GITHUB_API_BASE}/repos/{repo}/branches", headers=headers)
                if resp.status_code != 200:
                    raise RuntimeError(f"GitHub list branches failed: {resp.text}")
                return [b.get("name") for b in resp.json()]

            elif tool_name == "github_list_commits":
                repo = arguments.get("repo_name", "")
                limit = min(int(arguments.get("limit", 10)), 50)
                resp = await client.get(
                    f"{GITHUB_API_BASE}/repos/{repo}/commits",
                    headers=headers,
                    params={"per_page": limit},
                )
                if resp.status_code != 200:
                    raise RuntimeError(f"GitHub list commits failed: {resp.text}")
                return [
                    {
                        "sha": c.get("sha", "")[:7],
                        "message": c.get("commit", {}).get("message"),
                        "author": c.get("commit", {}).get("author", {}).get("name"),
                        "date": c.get("commit", {}).get("author", {}).get("date"),
                    }
                    for c in resp.json()
                ]

            elif tool_name == "github_search_code":
                repo = arguments.get("repo_name", "")
                query = arguments.get("query", "")
                resp = await client.get(
                    f"{GITHUB_API_BASE}/search/code",
                    headers=headers,
                    params={"q": f"{query}+repo:{repo}"},
                )
                if resp.status_code != 200:
                    raise RuntimeError(f"GitHub code search failed: {resp.text}")
                data = resp.json()
                return {
                    "total_count": data.get("total_count", 0),
                    "items": [
                        {"path": item.get("path"), "html_url": item.get("html_url")}
                        for item in data.get("items", [])[:10]
                    ],
                }

            elif tool_name == "github_list_issues":
                repo = arguments.get("repo_name", "")
                state = arguments.get("state", "open")
                limit = min(int(arguments.get("limit", 10)), 30)
                resp = await client.get(
                    f"{GITHUB_API_BASE}/repos/{repo}/issues",
                    headers=headers,
                    params={"state": state, "per_page": limit},
                )
                if resp.status_code != 200:
                    raise RuntimeError(f"GitHub list issues failed: {resp.text}")
                return [
                    {
                        "number": issue.get("number"),
                        "title": issue.get("title"),
                        "state": issue.get("state"),
                        "html_url": issue.get("html_url"),
                        "user": issue.get("user", {}).get("login"),
                        "created_at": issue.get("created_at"),
                    }
                    for issue in resp.json()
                    if "pull_request" not in issue  # Exclude pull requests
                ]

            elif tool_name == "github_create_issue":
                repo = arguments.get("repo_name", "")
                payload = {
                    "title": arguments.get("title"),
                    "body": arguments.get("body"),
                }
                if arguments.get("labels"):
                    payload["labels"] = arguments.get("labels")

                resp = await client.post(
                    f"{GITHUB_API_BASE}/repos/{repo}/issues",
                    headers=headers,
                    json=payload,
                )
                if resp.status_code not in (200, 201):
                    raise RuntimeError(f"GitHub create issue failed: {resp.text}")
                issue = resp.json()
                return {
                    "status": "created",
                    "number": issue.get("number"),
                    "title": issue.get("title"),
                    "html_url": issue.get("html_url"),
                    "state": issue.get("state"),
                }

            else:
                raise ValueError(f"Unknown GitHub tool: '{tool_name}'")

    def _execute_mock(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        repo = arguments.get("repo_name", "illusion-ai/core")
        if tool_name == "github_list_repositories":
            return [
                {
                    "name": "illusion-ai",
                    "full_name": "founder/illusion-ai",
                    "description": "Tamil Nadu & Central MSME OS with AI Agents and RAG",
                    "private": False,
                    "html_url": "https://github.com/founder/illusion-ai",
                    "language": "Python",
                    "stars": 42,
                },
                {
                    "name": "tn-msme-schemes-rag",
                    "full_name": "founder/tn-msme-schemes-rag",
                    "description": "Curated database of Tamil Nadu and Central Govt schemes",
                    "private": False,
                    "html_url": "https://github.com/founder/tn-msme-schemes-rag",
                    "language": "TypeScript",
                    "stars": 18,
                },
            ]
        elif tool_name == "github_get_repository":
            return {
                "full_name": repo,
                "description": "Tamil Nadu & Central MSME OS with AI Agents and RAG",
                "default_branch": "main",
                "open_issues_count": 3,
                "forks_count": 5,
                "stargazers_count": 42,
                "updated_at": "2026-11-23T10:00:00Z",
            }
        elif tool_name == "github_get_file_content":
            path = arguments.get("path", "README.md")
            return {
                "repo_name": repo,
                "path": path,
                "branch": arguments.get("branch", "main"),
                "size_bytes": 1280,
                "content": f"# {repo}\n\nAI-powered MSME operating system for Tamil Nadu entrepreneurs.\n\n## Features\n- LangGraph Intelligent Router\n- MCP Plugin Marketplace\n- Verified RAG Subsidies\n",
            }
        elif tool_name == "github_list_branches":
            return ["main", "feature/marketplace", "fix/oauth-guard"]
        elif tool_name == "github_list_commits":
            return [
                {"sha": "033c45f", "message": "fix: gate navbar navigation links and protect routes with AuthGuard", "author": "founder", "date": "2026-11-20T18:54:00Z"},
                {"sha": "332be9b", "message": "feat: implement Model Context Protocol (MCP 2.0) and GitHub OAuth 2.0 integration", "author": "founder", "date": "2026-11-20T12:00:00Z"},
            ]
        elif tool_name == "github_search_code":
            return {
                "total_count": 1,
                "items": [{"path": "backend/app/tools/router.py", "html_url": f"https://github.com/{repo}/blob/main/backend/app/tools/router.py"}],
            }
        elif tool_name == "github_list_issues":
            return [
                {"number": 12, "title": "Add Gmail draft creation support", "state": "open", "html_url": f"https://github.com/{repo}/issues/12", "user": "founder", "created_at": "2026-11-22T08:00:00Z"},
                {"number": 11, "title": "Upgrade Gemini embeddings model to text-embedding-004", "state": "closed", "html_url": f"https://github.com/{repo}/issues/11", "user": "founder", "created_at": "2026-11-18T14:00:00Z"},
            ]
        elif tool_name == "github_create_issue":
            return {
                "status": "created",
                "number": 13,
                "title": arguments.get("title"),
                "html_url": f"https://github.com/{repo}/issues/13",
                "state": "open",
            }
        raise ValueError(f"Unknown GitHub tool: '{tool_name}'")

    async def revoke(self, credentials: Dict[str, Any]) -> bool:
        # GitHub OAuth apps do not require token revocation endpoint calls, disconnecting locally suffices
        return True
