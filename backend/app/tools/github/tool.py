"""GitHub Tools implemented as BaseTool for Illusion AI Tool Registry."""

from typing import Dict, Any, Optional
from app.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult
try:
    from app.services.github_service import github_service
except ImportError:
    from backend.app.services.github_service import github_service


class GitHubGetProfileTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_get_profile",
            display_name="GitHub User Profile",
            description="Fetch authenticated user's GitHub profile including username, repositories count, and avatar.",
            parameters=[
                ToolParameter(name="user_id", type="string", description="User ID", required=False, default="default_user"),
            ],
            category="github",
            requires_auth=True,
        )

    async def execute(self, user_id: str = "default_user", **kwargs) -> ToolResult:
        try:
            profile = await github_service.github_get_profile(user_id=user_id)
            return ToolResult(tool_name="github_get_profile", success=True, data=profile)
        except Exception as e:
            return ToolResult(tool_name="github_get_profile", success=False, error=str(e))


class GitHubListRepositoriesTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_list_repositories",
            display_name="GitHub List Repositories",
            description="List repositories accessible to the user with stars, visibility, and updated times.",
            parameters=[
                ToolParameter(name="user_id", type="string", description="User ID", required=False, default="default_user"),
                ToolParameter(name="visibility", type="string", description="Visibility filter: 'all', 'public', 'private'", required=False, default="all"),
                ToolParameter(name="per_page", type="integer", description="Number of repos to return", required=False, default=20),
            ],
            category="github",
            requires_auth=True,
        )

    async def execute(self, user_id: str = "default_user", visibility: str = "all", per_page: int = 20, **kwargs) -> ToolResult:
        try:
            repos = await github_service.github_list_repositories(user_id=user_id, visibility=visibility, per_page=per_page)
            return ToolResult(tool_name="github_list_repositories", success=True, data=repos)
        except Exception as e:
            return ToolResult(tool_name="github_list_repositories", success=False, error=str(e))


class GitHubGetRepositoryTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_get_repository",
            display_name="GitHub Get Repository",
            description="Get metadata, stars, description, and default branch for a specific repository.",
            parameters=[
                ToolParameter(name="repo_name", type="string", description="Repository name, e.g. 'illusion-ai' or 'owner/repo'", required=True),
                ToolParameter(name="user_id", type="string", description="User ID", required=False, default="default_user"),
            ],
            category="github",
            requires_auth=True,
        )

    async def execute(self, repo_name: str, user_id: str = "default_user", **kwargs) -> ToolResult:
        try:
            repo = await github_service.github_get_repository(user_id=user_id, repo_name=repo_name)
            return ToolResult(tool_name="github_get_repository", success=True, data=repo)
        except Exception as e:
            return ToolResult(tool_name="github_get_repository", success=False, error=str(e))


class GitHubGetFileContentTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_get_file_content",
            display_name="GitHub Read File Content",
            description="Read and analyze the text content of a file (e.g. README.md, package.json, server.py) in a repository.",
            parameters=[
                ToolParameter(name="repo_name", type="string", description="Repository name, e.g. 'illusion-ai'", required=True),
                ToolParameter(name="file_path", type="string", description="Path to the file, e.g. 'README.md' or 'src/index.js'", required=True),
                ToolParameter(name="ref", type="string", description="Branch name or commit SHA", required=False, default=None),
                ToolParameter(name="user_id", type="string", description="User ID", required=False, default="default_user"),
            ],
            category="github",
            requires_auth=True,
        )

    async def execute(self, repo_name: str, file_path: str, ref: Optional[str] = None, user_id: str = "default_user", **kwargs) -> ToolResult:
        try:
            file_data = await github_service.github_get_file_content(user_id=user_id, repo_name=repo_name, file_path=file_path, ref=ref)
            return ToolResult(tool_name="github_get_file_content", success=True, data=file_data)
        except Exception as e:
            return ToolResult(tool_name="github_get_file_content", success=False, error=str(e))


class GitHubListBranchesTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_list_branches",
            display_name="GitHub List Branches",
            description="List branches in a GitHub repository.",
            parameters=[
                ToolParameter(name="repo_name", type="string", description="Repository name", required=True),
                ToolParameter(name="user_id", type="string", description="User ID", required=False, default="default_user"),
            ],
            category="github",
            requires_auth=True,
        )

    async def execute(self, repo_name: str, user_id: str = "default_user", **kwargs) -> ToolResult:
        try:
            branches = await github_service.github_list_branches(user_id=user_id, repo_name=repo_name)
            return ToolResult(tool_name="github_list_branches", success=True, data=branches)
        except Exception as e:
            return ToolResult(tool_name="github_list_branches", success=False, error=str(e))


class GitHubListCommitsTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_list_commits",
            display_name="GitHub List Commits",
            description="List recent commits, commit messages, and authors for a repository branch.",
            parameters=[
                ToolParameter(name="repo_name", type="string", description="Repository name", required=True),
                ToolParameter(name="branch", type="string", description="Branch name", required=False, default=None),
                ToolParameter(name="limit", type="integer", description="Number of commits to retrieve", required=False, default=10),
                ToolParameter(name="user_id", type="string", description="User ID", required=False, default="default_user"),
            ],
            category="github",
            requires_auth=True,
        )

    async def execute(self, repo_name: str, branch: Optional[str] = None, limit: int = 10, user_id: str = "default_user", **kwargs) -> ToolResult:
        try:
            commits = await github_service.github_list_commits(user_id=user_id, repo_name=repo_name, branch=branch, limit=limit)
            return ToolResult(tool_name="github_list_commits", success=True, data=commits)
        except Exception as e:
            return ToolResult(tool_name="github_list_commits", success=False, error=str(e))


class GitHubSearchCodeTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_search_code",
            display_name="GitHub Search Code",
            description="Search for specific code, functions, classes, or files in a repository.",
            parameters=[
                ToolParameter(name="repo_name", type="string", description="Repository name", required=True),
                ToolParameter(name="query", type="string", description="Search query string", required=True),
                ToolParameter(name="user_id", type="string", description="User ID", required=False, default="default_user"),
            ],
            category="github",
            requires_auth=True,
        )

    async def execute(self, repo_name: str, query: str, user_id: str = "default_user", **kwargs) -> ToolResult:
        try:
            res = await github_service.github_search_code(user_id=user_id, repo_name=repo_name, query=query)
            return ToolResult(tool_name="github_search_code", success=True, data=res)
        except Exception as e:
            return ToolResult(tool_name="github_search_code", success=False, error=str(e))
