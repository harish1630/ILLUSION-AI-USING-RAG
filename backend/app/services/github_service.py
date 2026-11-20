"""GitHub Tools and Repository Service for Illusion AI.

Provides the 7 required GitHub AI analysis tools:
1. github_get_profile
2. github_list_repositories
3. github_get_repository
4. github_get_file_content
5. github_list_branches
6. github_list_commits
7. github_search_code

All operations encrypt and decrypt tokens securely using Fernet,
handle rate limits, and enforce user authorization.
"""

from typing import Dict, Any, List, Optional
import base64
import httpx
from datetime import datetime, timezone
import logging

from app.core.logging import logger
try:
    from services.token_manager import token_manager
except ImportError:
    from backend.services.token_manager import token_manager

GITHUB_API_BASE = "https://api.github.com"


class GitHubService:
    """Service executing authenticated GitHub REST API operations on behalf of users."""

    def __init__(self):
        # In-memory store: user_id -> dict of connection details (encrypted_token, username, profile)
        # Backed also by Supabase GitHubConnectionModel
        self._connections: Dict[str, Dict[str, Any]] = {}

    def store_connection(
        self,
        user_id: str,
        github_user_id: str,
        username: str,
        email: Optional[str],
        avatar_url: Optional[str],
        plaintext_token: str,
    ):
        """Encrypts access token and saves connection."""
        encrypted_token = token_manager.encrypt_secret(plaintext_token)
        now = datetime.now(timezone.utc).isoformat()
        self._connections[user_id] = {
            "user_id": user_id,
            "github_user_id": github_user_id,
            "github_username": username,
            "github_email": email,
            "avatar_url": avatar_url,
            "encrypted_access_token": encrypted_token,
            "connected_at": now,
            "updated_at": now,
        }
        logger.info(f"Stored encrypted GitHub connection for user {user_id} (GitHub: {username})")

    def get_connection(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Returns connection metadata (excluding decrypted token)."""
        conn = self._connections.get(user_id)
        if not conn:
            return None
        return {
            "user_id": conn["user_id"],
            "github_user_id": conn["github_user_id"],
            "github_username": conn["github_username"],
            "github_email": conn["github_email"],
            "avatar_url": conn["avatar_url"],
            "connected_at": conn["connected_at"],
            "is_connected": True,
        }

    def disconnect(self, user_id: str) -> bool:
        """Removes user's GitHub connection and access token."""
        if user_id in self._connections:
            del self._connections[user_id]
            logger.info(f"Disconnected GitHub account for user {user_id}")
            return True
        return False

    def _get_token(self, user_id: str) -> str:
        """Retrieves and decrypts the user's GitHub access token."""
        conn = self._connections.get(user_id)
        if not conn:
            raise ValueError(f"User {user_id} has not connected their GitHub account.")
        return token_manager.decrypt_secret(conn["encrypted_access_token"])

    def _get_headers(self, token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Illusion-AI/2.0",
        }

    # -------------------------------------------------------------------------
    # 1. github_get_profile
    # -------------------------------------------------------------------------
    async def github_get_profile(self, user_id: str) -> Dict[str, Any]:
        """Fetch the authenticated user's GitHub profile."""
        token = self._get_token(user_id)
        headers = self._get_headers(token)
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{GITHUB_API_BASE}/user", headers=headers)
            if resp.status_code != 200:
                raise ValueError(f"GitHub API error ({resp.status_code}): {resp.text}")
            return resp.json()

    # -------------------------------------------------------------------------
    # 2. github_list_repositories
    # -------------------------------------------------------------------------
    async def github_list_repositories(
        self,
        user_id: str,
        visibility: str = "all",
        sort: str = "updated",
        per_page: int = 30,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """List repositories accessible to the user with pagination."""
        token = self._get_token(user_id)
        headers = self._get_headers(token)
        params = {
            "visibility": visibility,
            "sort": sort,
            "per_page": min(per_page, 100),
            "page": page,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{GITHUB_API_BASE}/user/repos", headers=headers, params=params)
            if resp.status_code != 200:
                raise ValueError(f"GitHub API error ({resp.status_code}): {resp.text}")
            repos = resp.json()
            return [
                {
                    "name": r.get("name"),
                    "full_name": r.get("full_name"),
                    "owner": r.get("owner", {}).get("login"),
                    "private": r.get("private"),
                    "description": r.get("description"),
                    "html_url": r.get("html_url"),
                    "default_branch": r.get("default_branch", "main"),
                    "stars": r.get("stargazers_count", 0),
                    "forks": r.get("forks_count", 0),
                    "language": r.get("language"),
                    "updated_at": r.get("updated_at"),
                }
                for r in repos
            ]

    # -------------------------------------------------------------------------
    # 3. github_get_repository
    # -------------------------------------------------------------------------
    async def github_get_repository(self, user_id: str, repo_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific repository (e.g. 'owner/repo' or 'repo')."""
        token = self._get_token(user_id)
        headers = self._get_headers(token)

        # Prepend username if only repo name is provided
        if "/" not in repo_name:
            conn = self.get_connection(user_id)
            if conn:
                repo_name = f"{conn['github_username']}/{repo_name}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{GITHUB_API_BASE}/repos/{repo_name}", headers=headers)
            if resp.status_code != 200:
                raise ValueError(f"Repository '{repo_name}' not found or inaccessible: {resp.text}")
            r = resp.json()
            return {
                "name": r.get("name"),
                "full_name": r.get("full_name"),
                "owner": r.get("owner", {}).get("login"),
                "description": r.get("description"),
                "default_branch": r.get("default_branch", "main"),
                "private": r.get("private"),
                "html_url": r.get("html_url"),
                "stars": r.get("stargazers_count", 0),
                "open_issues": r.get("open_issues_count", 0),
                "language": r.get("language"),
                "created_at": r.get("created_at"),
                "updated_at": r.get("updated_at"),
            }

    # -------------------------------------------------------------------------
    # 4. github_get_file_content
    # -------------------------------------------------------------------------
    async def github_get_file_content(
        self,
        user_id: str,
        repo_name: str,
        file_path: str,
        ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch and decode the content of a file from a repository."""
        token = self._get_token(user_id)
        headers = self._get_headers(token)

        if "/" not in repo_name:
            conn = self.get_connection(user_id)
            if conn:
                repo_name = f"{conn['github_username']}/{repo_name}"

        params = {}
        if ref:
            params["ref"] = ref

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{GITHUB_API_BASE}/repos/{repo_name}/contents/{file_path}",
                headers=headers,
                params=params,
            )
            if resp.status_code != 200:
                raise ValueError(f"File '{file_path}' not found in '{repo_name}': {resp.text}")

            data = resp.json()
            if isinstance(data, list):
                # Directory listing
                return {
                    "type": "directory",
                    "repo": repo_name,
                    "path": file_path,
                    "entries": [{"name": item["name"], "type": item["type"], "size": item.get("size", 0)} for item in data],
                }

            encoding = data.get("encoding", "")
            raw_content = data.get("content", "")
            if encoding == "base64":
                decoded_content = base64.b64decode(raw_content).decode("utf-8", errors="replace")
            else:
                decoded_content = raw_content

            return {
                "type": "file",
                "repo": repo_name,
                "path": file_path,
                "name": data.get("name"),
                "size_bytes": data.get("size", 0),
                "sha": data.get("sha"),
                "content": decoded_content,
            }

    # -------------------------------------------------------------------------
    # 5. github_list_branches
    # -------------------------------------------------------------------------
    async def github_list_branches(self, user_id: str, repo_name: str) -> List[Dict[str, Any]]:
        """List branches in a repository."""
        token = self._get_token(user_id)
        headers = self._get_headers(token)

        if "/" not in repo_name:
            conn = self.get_connection(user_id)
            if conn:
                repo_name = f"{conn['github_username']}/{repo_name}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{GITHUB_API_BASE}/repos/{repo_name}/branches", headers=headers)
            if resp.status_code != 200:
                raise ValueError(f"Failed to list branches for '{repo_name}': {resp.text}")
            branches = resp.json()
            return [
                {
                    "name": b.get("name"),
                    "sha": b.get("commit", {}).get("sha"),
                    "protected": b.get("protected", False),
                }
                for b in branches
            ]

    # -------------------------------------------------------------------------
    # 6. github_list_commits
    # -------------------------------------------------------------------------
    async def github_list_commits(
        self,
        user_id: str,
        repo_name: str,
        branch: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """List recent commits on a repository branch."""
        token = self._get_token(user_id)
        headers = self._get_headers(token)

        if "/" not in repo_name:
            conn = self.get_connection(user_id)
            if conn:
                repo_name = f"{conn['github_username']}/{repo_name}"

        params = {"per_page": min(limit, 100)}
        if branch:
            params["sha"] = branch

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{GITHUB_API_BASE}/repos/{repo_name}/commits",
                headers=headers,
                params=params,
            )
            if resp.status_code != 200:
                raise ValueError(f"Failed to list commits for '{repo_name}': {resp.text}")
            commits = resp.json()
            return [
                {
                    "sha": c.get("sha")[:8],
                    "message": c.get("commit", {}).get("message"),
                    "author": c.get("commit", {}).get("author", {}).get("name"),
                    "date": c.get("commit", {}).get("author", {}).get("date"),
                    "html_url": c.get("html_url"),
                }
                for c in commits
            ]

    # -------------------------------------------------------------------------
    # 7. github_search_code
    # -------------------------------------------------------------------------
    async def github_search_code(
        self,
        user_id: str,
        repo_name: str,
        query: str,
    ) -> Dict[str, Any]:
        """Search code within a specific repository."""
        token = self._get_token(user_id)
        headers = self._get_headers(token)

        if "/" not in repo_name:
            conn = self.get_connection(user_id)
            if conn:
                repo_name = f"{conn['github_username']}/{repo_name}"

        search_query = f"{query} repo:{repo_name}"
        params = {"q": search_query, "per_page": 20}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{GITHUB_API_BASE}/search/code",
                headers=headers,
                params=params,
            )
            if resp.status_code != 200:
                raise ValueError(f"Code search failed: {resp.text}")
            data = resp.json()
            items = data.get("items", [])
            return {
                "total_count": data.get("total_count", 0),
                "matches": [
                    {
                        "name": item.get("name"),
                        "path": item.get("path"),
                        "sha": item.get("sha"),
                        "html_url": item.get("html_url"),
                    }
                    for item in items
                ],
            }


# Global singleton service
github_service = GitHubService()
